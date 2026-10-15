import tkinter as tk
from tkinter import simpledialog
import json
import math
import time
import os
import sys
import random
import ctypes
from input_hook import InputHook
from api_server import start_server
from tkinterdnd2 import DND_FILES, TkinterDnD

def darken_color(hex_color, amount=0.7):
    hex_color = hex_color.lstrip('#')
    try:
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = max(0, int(r * amount))
        g = max(0, int(g * amount))
        b = max(0, int(b * amount))
        return f"#{r:02x}{g:02x}{b:02x}"
    except:
        return "#222222"

def apply_spring(current, velocity, target, tension=0.2, dampening=0.6):
    displacement = target - current
    spring_force = displacement * tension
    velocity = (velocity + spring_force) * dampening
    current += velocity
    return current, velocity

class DeskCat:
    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        
        self.transparent_color = "#000001"
        self.root.wm_attributes("-transparentcolor", self.transparent_color)
        self.root.config(bg=self.transparent_color)

        self.width = 200
        self.height = 200
        
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.x = screen_w - self.width - 50
        self.y = screen_h - self.height - 50
        self.root.geometry(f"{self.width}x{self.height}+{self.x}+{self.y}")

        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, 
                                bg=self.transparent_color, highlightthickness=0)
        self.canvas.pack()

        try:
            with open("config.json") as f:
                self.config = json.load(f)
        except:
            self.config = {"base_color": "#ffffff", "spot_color": "#ff9900", "eye_color": "#222222"}

        self.state = "idle"
        self.frame = 0
        self.mouse_global_x = 0
        self.mouse_global_y = 0
        self.mouse_history = []
        self.parts = {}
        
        self.target_x = 0
        self.walk_start_x = 0
        self.walk_duration = 60
        self.direction = 1
        self.last_random_action = time.time()
        
        self.blink_timer = time.time() + random.uniform(2, 6)
        self.blink_end = 0
        self.is_blinking = False
        
        self.fatigue = 0
        self.idle_start_time = time.time()
        self.hunt_frames = 0
        
        self.parallax_x = 0
        self.parallax_y = 0
        
        self.is_hidden_by_fullscreen = False
        
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.vel_scale_x = 0.0
        self.vel_scale_y = 0.0
        self.target_scale_x = 1.0
        self.target_scale_y = 1.0
        
        self.wobble_x = 0.0
        self.vel_wobble_x = 0.0
        self.target_wobble_x = 0.0
        
        self._drag_data = {"x": 0, "y": 0, "dragging": False, "history": []}
        self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.canvas.bind("<ButtonRelease-1>", self.on_drag_stop)
        self.canvas.bind("<B1-Motion>", self.on_drag_motion)
        self.canvas.bind("<Enter>", self.on_enter)
        self.canvas.bind("<Leave>", self.on_leave)
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<Button-3>", self.show_context_menu)
        
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)

        self.input_hook = InputHook()
        self.input_hook.start()
        
        start_server(self.input_hook.event_queue)

        self.last_stretch_time = time.time()
        self.message = ""
        self.message_timeout = 0
        self.show_note = False
        self.note_text = ""
        self.is_overheat = False
        self.muted = False
        
        self.draw_cat()
        self.update_loop()

    def on_drag_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self._drag_data["dragging"] = True
        self._drag_data["history"] = []
        self.state = "stretch"
        self.frame = 0

    def on_drag_stop(self, event):
        self._drag_data["dragging"] = False
        if self.state in ["stretch", "wobble"]:
            self.state = "idle"

    def on_drag_motion(self, event):
        deltax = event.x - self._drag_data["x"]
        deltay = event.y - self._drag_data["y"]
        self.x += deltax
        self.y += deltay
        self.root.geometry(f"+{int(self.x)}+{int(self.y)}")
        
        self._drag_data["history"].append(deltax)
        if len(self._drag_data["history"]) > 10:
            self._drag_data["history"].pop(0)
            
        changes = 0
        for i in range(1, len(self._drag_data["history"])):
            if self._drag_data["history"][i] * self._drag_data["history"][i-1] < 0 and abs(self._drag_data["history"][i]) > 2:
                changes += 1
                
        if changes >= 3:
            self.state = "wobble"
            self.frame = 0 
        else:
            self.state = "stretch"

    def on_enter(self, event):
        pass 
    
    def on_leave(self, event):
        if not self._drag_data["dragging"] and self.state == "purr":
            self.state = "idle"
            
    def on_motion(self, event):
        if not self._drag_data["dragging"] and self.state in ["idle", "purr"]:
            if event.y < self.height//2 + 10:
                self.state = "purr"
            else:
                self.state = "idle"

    def show_context_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0)
        
        appearance_menu = tk.Menu(menu, tearoff=0)
        appearance_menu.add_command(label="Orange & White", command=lambda: self.change_appearance("#ffffff", "#ff9900", "#222222"))
        appearance_menu.add_command(label="Midnight Black", command=lambda: self.change_appearance("#2b2b2b", "#1a1a1a", "#e6e600"))
        appearance_menu.add_command(label="Gray Tabby", command=lambda: self.change_appearance("#888888", "#555555", "#33ff33"))
        appearance_menu.add_command(label="Siamese", command=lambda: self.change_appearance("#fff3e0", "#4e342e", "#42a5f5"))
        menu.add_cascade(label="Appearance", menu=appearance_menu)
        menu.add_separator()
        
        menu.add_command(label="Pin Note", command=self.pin_note)
        mute_label = "Unmute Meows" if self.muted else "Mute Meows"
        menu.add_command(label=mute_label, command=self.toggle_mute)
        menu.add_command(label="Toggle Start with Windows", command=self.toggle_startup)
        menu.add_separator()
        menu.add_command(label="Quit", command=self.quit_app)
        menu.tk_popup(event.x_root, event.y_root)

    def change_appearance(self, base_color, spot_color, eye_color):
        self.config["base_color"] = base_color
        self.config["spot_color"] = spot_color
        self.config["eye_color"] = eye_color
        try:
            with open("config.json", "w") as f:
                json.dump(self.config, f)
        except Exception as e:
            print(f"Error saving config: {e}")
        self.draw_cat()
        self.trigger_message("Purr...", duration=2)

    def pin_note(self):
        note = simpledialog.askstring("Pin Note", "What should DeskCat hold?", parent=self.root)
        if note:
            self.show_note = True
            self.note_text = note
        else:
            self.show_note = False

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            self.trigger_message("Muted")
        else:
            self.trigger_message("Unmuted!")

    def toggle_startup(self):
        startup_dir = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        bat_path = os.path.join(startup_dir, 'deskcat.bat')
        if os.path.exists(bat_path):
            os.remove(bat_path)
            self.trigger_message("Removed from startup")
        else:
            current_script = os.path.abspath(sys.argv[0])
            work_dir = os.path.dirname(current_script)
            python_exe = sys.executable
            with open(bat_path, "w") as f:
                f.write(f'@echo off\ncd /d "{work_dir}"\nstart "" "{python_exe}" "{current_script}"')
            self.trigger_message("Added to startup")

    def quit_app(self):
        self.root.quit()
        os._exit(0)

    def on_drop(self, event):
        self.state = "eat"
        self.frame = 0

    def trigger_message(self, text, duration=5):
        if self.muted and text == "Meow!":
            return
        self.message = text
        self.message_timeout = time.time() + duration

    def draw_cat(self):
        self.canvas.delete("all")
        c_base = "#ff5555" if self.is_overheat else self.config.get("base_color", "#ffffff")
        c_spot = "#ff5555" if self.is_overheat else self.config.get("spot_color", "#ff9900")
        c_eye = self.config.get("eye_color", "#222222")

        c_outline_base = darken_color(c_base, 0.6)
        c_outline_spot = darken_color(c_spot, 0.6)
        c_self_shadow = darken_color(c_base, 0.85)

        cx, cy = self.width//2, self.height//2 + 30
        self.parts.clear()

        tail_wave = math.sin(self.frame * 0.2) * 8 if self.state in ["purr", "wobble"] else math.sin(self.frame * 0.1) * 3
        self.parts["tail"] = self.canvas.create_polygon(
            cx+15, cy+15, cx+35, cy+35+tail_wave, cx+45+tail_wave, cy+25, cx+20, cy+10,
            fill=c_spot, outline=c_outline_spot, width=2, smooth=True
        )

        self.parts["body_shadow"] = self.canvas.create_polygon(
            cx-30, cy-5, cx+30, cy-5, cx+30, cy+28, cx-30, cy+28,
            fill=c_self_shadow, outline="", smooth=True
        )
        
        self.parts["body"] = self.canvas.create_polygon(
            cx-28, cy-10, cx+28, cy-10, cx+28, cy+25, cx-28, cy+25,
            fill=c_base, outline=c_outline_base, width=2, smooth=True
        )

        self.parts["ear_l"] = self.canvas.create_polygon(
            cx-25, cy-25, cx-15, cy-50, cx-5, cy-35,
            fill=c_base, outline=c_outline_base, width=2, smooth=True
        )
        self.parts["ear_l_inner"] = self.canvas.create_polygon(
            cx-20, cy-30, cx-15, cy-40, cx-10, cy-35,
            fill="#ffaaaa", outline="", smooth=True
        )
        self.parts["ear_r"] = self.canvas.create_polygon(
            cx+5, cy-35, cx+15, cy-50, cx+25, cy-25,
            fill=c_spot, outline=c_outline_spot, width=2, smooth=True
        )
        self.parts["ear_r_inner"] = self.canvas.create_polygon(
            cx+10, cy-35, cx+15, cy-40, cx+20, cy-30,
            fill="#ffaaaa", outline="", smooth=True
        )

        self.parts["head"] = self.canvas.create_polygon(
            cx-28, cy-40, cx+28, cy-40, cx+32, cy-5, cx-32, cy-5,
            fill=c_base, outline=c_outline_base, width=2, smooth=True
        )
        
        self.parts["spot"] = self.canvas.create_polygon(
            cx-8, cy-40, cx+22, cy-40, cx+28, cy-15, cx+2, cy-15,
            fill=c_spot, outline="", smooth=True
        )

        if self.state in ["purr", "hunt", "jump"]:
            self.parts["blush_l"] = self.canvas.create_oval(cx-23, cy-18, cx-11, cy-11, fill="#ff9999", outline="")
            self.parts["blush_r"] = self.canvas.create_oval(cx+11, cy-18, cx+23, cy-11, fill="#ff9999", outline="")
        else:
            self.parts["blush_l"] = self.canvas.create_oval(cx-22, cy-18, cx-12, cy-12, fill="#ffbbbb", outline="")
            self.parts["blush_r"] = self.canvas.create_oval(cx+12, cy-18, cx+22, cy-12, fill="#ffbbbb", outline="")

        for i, wy in enumerate([-16, -13, -10]):
            self.parts[f"whisker_l_{i}"] = self.canvas.create_line(cx-24, wy+cy, cx-34, wy+cy+(i-1)*3, fill=c_outline_base, width=1, smooth=True)
            self.parts[f"whisker_r_{i}"] = self.canvas.create_line(cx+24, wy+cy, cx+34, wy+cy+(i-1)*3, fill=c_outline_base, width=1, smooth=True)

        paw_w, paw_h = 14, 16
        self.parts["paw_bl"] = self.canvas.create_oval(cx-24, cy+18, cx-24+paw_w, cy+18+paw_h, fill=c_base, outline=c_outline_base, width=2)
        self.parts["paw_br"] = self.canvas.create_oval(cx+10, cy+18, cx+10+paw_w, cy+18+paw_h, fill=c_base, outline=c_outline_base, width=2)

        self.parts["paw_fl"] = self.canvas.create_oval(cx-14, cy+18, cx-14+paw_w, cy+18+paw_h, fill=c_base, outline=c_outline_base, width=2)
        self.parts["paw_fr"] = self.canvas.create_oval(cx, cy+18, cx+paw_w, cy+18+paw_h, fill=c_base, outline=c_outline_base, width=2)

        for i, (px, py) in enumerate([(cx-24, cy+18), (cx+10, cy+18), (cx-14, cy+18), (cx, cy+18)]):
            self.parts[f"toe_{i}_1"] = self.canvas.create_line(px+4, py+10, px+4, py+14, fill=c_outline_base, width=1)
            self.parts[f"toe_{i}_2"] = self.canvas.create_line(px+9, py+10, px+9, py+14, fill=c_outline_base, width=1)

        self.parts["nose"] = self.canvas.create_polygon(
            cx-3, cy-17, cx+3, cy-17, cx, cy-14, fill="#ff99aa", outline="", smooth=True
        )

        if self.state not in ["eat"]:
            self.parts["mouth_l"] = self.canvas.create_arc(cx-5, cy-16, cx, cy-11, start=180, extent=180, style=tk.ARC, outline=c_eye, width=2)
            self.parts["mouth_r"] = self.canvas.create_arc(cx, cy-16, cx+5, cy-11, start=180, extent=180, style=tk.ARC, outline=c_eye, width=2)

        force_blink = (self.is_blinking or (self.state == "stretch" and not self._drag_data["dragging"]) or self.state == "sleep") and self.state not in ["purr", "eat", "thinking", "hunt"]

        if force_blink:
            self.parts["eye_l"] = self.canvas.create_line(cx-14, cy-22, cx-6, cy-22, fill=c_eye, width=3, capstyle=tk.ROUND)
            self.parts["eye_r"] = self.canvas.create_line(cx+6, cy-22, cx+14, cy-22, fill=c_eye, width=3, capstyle=tk.ROUND)
        elif self.state == "thinking":
            self.parts["eye_l"] = self.canvas.create_line(cx-14, cy-22, cx-6, cy-22, fill=c_eye, width=3, capstyle=tk.ROUND)
            self.parts["eye_r"] = self.canvas.create_line(cx+6, cy-22, cx+14, cy-22, fill=c_eye, width=3, capstyle=tk.ROUND)
        elif self.state == "purr":
            self.parts["eye_l"] = self.canvas.create_arc(cx-14, cy-24, cx-6, cy-18, start=0, extent=180, style=tk.ARC, outline=c_eye, width=3)
            self.parts["eye_r"] = self.canvas.create_arc(cx+6, cy-24, cx+14, cy-18, start=0, extent=180, style=tk.ARC, outline=c_eye, width=3)
        elif self.state == "hunt":
            self.parts["eye_l"] = self.canvas.create_oval(cx-16, cy-30, cx-4, cy-14, fill=c_eye, outline="")
            self.parts["eye_r"] = self.canvas.create_oval(cx+4, cy-30, cx+16, cy-14, fill=c_eye, outline="")
            self.parts["catch_l"] = self.canvas.create_oval(cx-12, cy-27, cx-8, cy-23, fill="white", outline="")
            self.parts["catch_r"] = self.canvas.create_oval(cx+8, cy-27, cx+12, cy-23, fill="white", outline="")
        elif self.state == "eat":
            self.parts["eye_l"] = self.canvas.create_line(cx-14, cy-20, cx-6, cy-24, fill=c_eye, width=3, capstyle=tk.ROUND)
            self.parts["eye_r"] = self.canvas.create_line(cx+6, cy-24, cx+14, cy-20, fill=c_eye, width=3, capstyle=tk.ROUND)
        else:
            self.parts["eye_bg_l"] = self.canvas.create_oval(cx-16, cy-30, cx-4, cy-14, fill=c_eye, outline="")
            self.parts["eye_bg_r"] = self.canvas.create_oval(cx+4, cy-30, cx+16, cy-14, fill=c_eye, outline="")
            
            dx = self.mouse_global_x - (self.x + cx)
            dy = self.mouse_global_y - (self.y + cy)
            dist = math.hypot(dx, dy)
            if dist > 0:
                px = (dx / dist) * 1.5
                py = (dy / dist) * 1.5
            else:
                px, py = 0, 0
            
            self.parts["pupil_l"] = self.canvas.create_oval(cx-13+px, cy-27+py, cx-7+px, cy-21+py, fill="white", outline="")
            self.parts["pupil_r"] = self.canvas.create_oval(cx+7+px, cy-27+py, cx+13+px, cy-21+py, fill="white", outline="")
            self.parts["pupil2_l"] = self.canvas.create_oval(cx-9+px, cy-20+py, cx-7+px, cy-18+py, fill="white", outline="")
            self.parts["pupil2_r"] = self.canvas.create_oval(cx+11+px, cy-20+py, cx+13+px, cy-18+py, fill="white", outline="")

        if self.state == "eat":
            mouth_h = 2 if self.frame % 4 < 2 else 10
            self.parts["mouth"] = self.canvas.create_oval(cx-5, cy-15, cx+5, cy-15+mouth_h, fill=c_eye, outline="")
            if self.frame < 15:
                doc_y = cy - 40 + self.frame * 3
                self.parts["doc"] = self.canvas.create_rectangle(cx-8, doc_y, cx+8, doc_y+10, fill="white", outline="#999999")
                self.canvas.create_line(cx-5, doc_y+3, cx+5, doc_y+3, fill="#999999")
                self.canvas.create_line(cx-5, doc_y+6, cx+5, doc_y+6, fill="#999999")

        if self.is_overheat:
            self.canvas.create_oval(cx-15, cy-60 - (self.frame%10), cx-5, cy-50 - (self.frame%10), fill="white", outline="")
            self.canvas.create_oval(cx+5, cy-55 - (self.frame%10), cx+15, cy-45 - (self.frame%10), fill="white", outline="")

        if time.time() < self.message_timeout:
            self.canvas.create_rectangle(cx-40, cy-80, cx+40, cy-50, fill="white", outline=c_outline_base, width=2)
            self.canvas.create_text(cx, cy-65, text=self.message, font=("Arial", 8, "bold"), fill=c_eye)

        if self.show_note:
            self.canvas.create_rectangle(cx+30, cy-60, cx+70, cy-20, fill="#ffff88", outline=c_outline_base, width=1)
            self.canvas.create_text(cx+50, cy-40, text=self.note_text, font=("Arial", 7), width=35)
            
        if self.state == "sleep":
            z_frame = self.frame % 120
            if z_frame > 0:
                self.canvas.create_text(cx+10 + z_frame*0.2, cy-40 - z_frame*0.5, text="z", font=("Arial", 8, "bold"), fill=c_outline_base)
            if z_frame > 40:
                z2 = z_frame - 40
                self.canvas.create_text(cx+20 + z2*0.2, cy-50 - z2*0.5, text="Z", font=("Arial", 10, "bold"), fill=c_outline_base)
            if z_frame > 80:
                z3 = z_frame - 80
                self.canvas.create_text(cx+35 + z3*0.2, cy-65 - z3*0.5, text="Z", font=("Arial", 14, "bold"), fill=c_outline_base)

    def process_events(self):
        while not self.input_hook.event_queue.empty():
            evt = self.input_hook.event_queue.get()
            if evt['type'] == 'mouse_move':
                if self.state == "sleep":
                    mx = self.mouse_global_x - (self.x + self.width//2)
                    my = self.mouse_global_y - (self.y + self.height//2 + 30)
                    if math.hypot(mx, my) < 80:
                        self.state = "idle"
                        self.trigger_message("Yawn~", duration=2)
                
                self.mouse_global_x = evt['x']
                self.mouse_global_y = evt['y']
                
                self.mouse_history.append((evt['x'], evt['y'], time.time()))
                current_time = time.time()
                self.mouse_history = [p for p in self.mouse_history if current_time - p[2] < 0.1]
                
                if len(self.mouse_history) > 2 and self.state not in ["knead", "eat", "jump", "thinking", "stretch", "wobble", "purr", "walk", "pounce", "fall"]:
                    dist = math.hypot(self.mouse_history[-1][0] - self.mouse_history[0][0], 
                                      self.mouse_history[-1][1] - self.mouse_history[0][1])
                    if dist > 200:
                        if self.state != "hunt":
                            self.state = "hunt"
                            self.hunt_frames = 0
                    elif self.state == "hunt":
                        self.state = "idle"

            elif evt['type'] == 'key_press':
                if self.state == "sleep":
                    self.state = "idle"
                    self.trigger_message("Yawn~", duration=2)
                elif self.state not in ["thinking", "eat", "jump"]:
                    self.state = "knead"
                    self.frame = 0
                self.is_overheat = evt.get('wpm', 0) > 80
            elif evt['type'] == 'mouse_scroll':
                if self.state not in ["thinking", "eat", "jump"]:
                    self.state = "scroll"
                    self.frame = 0
            elif evt['type'] == 'ai_status':
                if evt['status'] == 'thinking':
                    self.state = "thinking"
                elif evt['status'] == 'done':
                    self.state = "jump"
                    self.frame = 0
                    self.trigger_message("Meow!")
            elif evt['type'] == 'ai_message':
                self.trigger_message(evt['message'])

    def check_fullscreen(self):
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd: return False
            
            rect = ctypes.wintypes.RECT()
            ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
            
            monitor = ctypes.windll.user32.MonitorFromWindow(hwnd, 2)
            
            class MONITORINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.wintypes.DWORD),
                            ("rcMonitor", ctypes.wintypes.RECT),
                            ("rcWork", ctypes.wintypes.RECT),
                            ("dwFlags", ctypes.wintypes.DWORD)]
            mi = MONITORINFO()
            mi.cbSize = ctypes.sizeof(MONITORINFO)
            ctypes.windll.user32.GetMonitorInfoW(monitor, ctypes.byref(mi))
            
            if (rect.left <= mi.rcMonitor.left and 
                rect.top <= mi.rcMonitor.top and 
                rect.right >= mi.rcMonitor.right and 
                rect.bottom >= mi.rcMonitor.bottom):
                
                buff = ctypes.create_unicode_buffer(256)
                ctypes.windll.user32.GetClassNameW(hwnd, buff, 256)
                if buff.value not in ["Progman", "WorkerW"]:
                    return True
            return False
        except:
            return False

    def update_loop(self):
        self.frame += 1
        
        if self.frame % 15 == 0:
            is_fs = self.check_fullscreen()
            if is_fs and not self.is_hidden_by_fullscreen:
                self.root.withdraw()
                self.is_hidden_by_fullscreen = True
            elif not is_fs and self.is_hidden_by_fullscreen:
                self.root.deiconify()
                self.is_hidden_by_fullscreen = False
                
        if self.is_hidden_by_fullscreen:
            self.root.after(30, self.update_loop)
            return

        self.process_events()
        
        if time.time() > self.blink_timer:
            self.is_blinking = True
            self.blink_timer = time.time() + random.uniform(2, 6)
            self.blink_end = time.time() + 0.15
        if self.is_blinking and time.time() > self.blink_end:
            self.is_blinking = False
            
        if self.state != "idle":
            self.idle_start_time = time.time()
            if self.state == "knead":
                self.fatigue += 1
        
        if self.state == "idle" and time.time() - self.last_random_action > 15:
            idle_duration = time.time() - self.idle_start_time
            if random.random() < 0.005:
                if idle_duration > 300: 
                    action = random.choice(["sleep", "sleep", "stretch"])
                elif self.fatigue > 300 or idle_duration > 60:
                    action = random.choice(["stretch", "walk"])
                else:
                    action = "walk"
                    
                if action == "sleep":
                    self.state = "sleep"
                    self.frame = 0
                elif action == "stretch":
                    self.state = "stretch"
                    self.frame = 0
                    self.trigger_message("Big stretch!", duration=3)
                    self.fatigue = 0
                else:
                    self.state = "walk"
                    self.frame = 0
                    self.walk_start_x = self.x
                    screen_w = self.root.winfo_screenwidth()
                    self.target_x = random.randint(0, screen_w - self.width)
                    self.direction = 1 if self.target_x > self.x else -1
                    dist = abs(self.target_x - self.x)
                    self.walk_duration = max(30, int(dist / 3))
                self.last_random_action = time.time()

        if self.state == "knead" and self.frame > 10:
            self.state = "idle"
        elif self.state == "jump" and self.frame > 30:
            self.state = "idle"
        elif self.state == "scroll" and self.frame > 10:
            self.state = "idle"
        elif self.state == "eat" and self.frame > 20:
            self.state = "idle"
            self.trigger_message("Burp!", duration=2)
        elif self.state == "stretch" and not self._drag_data["dragging"] and self.frame > 50:
            self.state = "idle"
            
        if self.state == "hunt":
            self.hunt_frames += 1
            if self.hunt_frames > 25:
                self.state = "pounce"
                self.frame = 0
                self.pounce_start_x = self.x
                self.pounce_start_y = self.y
                screen_w = self.root.winfo_screenwidth()
                screen_h = self.root.winfo_screenheight()
                target_x = self.mouse_global_x - self.width//2
                target_y = self.mouse_global_y - self.height//2
                self.pounce_target_x = max(0, min(target_x, screen_w - self.width))
                self.pounce_target_y = max(0, min(target_y, screen_h - self.height))
        
        self.draw_cat()
        
        def move_parts(parts_list, dx, dy):
            for p in parts_list:
                if p in self.parts:
                    self.canvas.move(self.parts[p], dx, dy)
        
        cx, cy = self.width//2, self.height//2 + 30
        
        head_base = ["head", "spot"]
        face_parts = [
            "eye_l", "eye_r", "eye_bg_l", "eye_bg_r", "pupil_l", "pupil_r", 
            "pupil2_l", "pupil2_r", "catch_l", "catch_r", "blush_l", "blush_r",
            "nose", "mouth", "mouth_l", "mouth_r"
        ]
        for i in range(3):
            face_parts.extend([f"whisker_l_{i}", f"whisker_r_{i}"])
            
        head_parts = head_base + face_parts
        ear_parts = ["ear_l", "ear_r", "ear_l_inner", "ear_r_inner"]
            
        paw_fl_parts = ["paw_fl", "toe_2_1", "toe_2_2"]
        paw_fr_parts = ["paw_fr", "toe_3_1", "toe_3_2"]
        paw_bl_parts = ["paw_bl", "toe_0_1", "toe_0_2"]
        paw_br_parts = ["paw_br", "toe_1_1", "toe_1_2"]
        body_parts = ["body", "body_shadow"]
        
        self.target_scale_x = 1.0
        self.target_scale_y = 1.0
        self.target_wobble_x = 0.0

        if self.state == "idle":
            t = (self.frame % 60) / 60.0
            if t < 0.3:
                breathe = math.sin((t / 0.3) * (math.pi / 2))
            else:
                breathe = math.cos(((t - 0.3) / 0.7) * (math.pi / 2))
            breathe_offset = breathe * 2
            
            move_parts(head_parts, 0, breathe_offset)
            move_parts(ear_parts, 0, breathe_offset * 0.7) 
            
            self.target_scale_x = 1.0 + breathe*0.015
            self.target_scale_y = 1.0 - breathe*0.015
                
        elif self.state == "knead":
            bob = math.sin(self.frame * 0.5) * 2
            move_parts(head_parts, 0, bob)
            move_parts(ear_parts, 0, bob * 0.5)
            move_parts(body_parts, 0, bob*0.5)
            
            paw_speed = 1.2
            if (self.frame * paw_speed) % 4 < 2:
                move_parts(paw_fl_parts, 0, -8)
            else:
                move_parts(paw_fr_parts, 0, -8)
                
        elif self.state == "jump":
            progress = self.frame / 30.0
            if progress <= 1.0:
                height = 60
                dy = -4 * height * progress * (1 - progress)
                
                if progress < 0.2:
                    self.target_scale_x = 1.2
                    self.target_scale_y = 0.8
                elif progress < 0.5:
                    self.target_scale_x = 0.8
                    self.target_scale_y = 1.3
                elif progress > 0.8:
                    self.target_scale_x = 1.2
                    self.target_scale_y = 0.8
                    
                self.canvas.move("all", 0, dy)
                
        elif self.state == "stretch":
            if self._drag_data["dragging"]:
                self.target_scale_y = 1.35
                self.target_scale_x = 0.85
                move_parts(head_parts, 0, -12)
                move_parts(ear_parts, 0, -12)
            else:
                progress = min(1.0, self.frame / 20.0) if self.frame < 30 else max(0.0, 1.0 - (self.frame - 30) / 20.0)
                ease = progress * progress * (3 - 2 * progress)
                
                if self.frame < 30:
                    self.target_scale_x = 1.3
                    self.target_scale_y = 0.75
                else:
                    self.target_scale_x = 1.0
                    self.target_scale_y = 1.0
                    
                move_parts(head_parts, -20 * ease, 15 * ease)
                move_parts(ear_parts, -20 * ease, 15 * ease)
                move_parts(paw_fl_parts, -25 * ease, 0)
                move_parts(paw_fr_parts, -25 * ease, 0)
                move_parts(paw_bl_parts, 15 * ease, 0)
                move_parts(paw_br_parts, 15 * ease, 0)
                self.canvas.move(self.parts["tail"], 10 * ease, -20 * ease)
            
        elif self.state == "walk":
            progress = min(1.0, self.frame / float(self.walk_duration))
            ease = progress * progress * (3 - 2 * progress)
            self.x = self.walk_start_x + (self.target_x - self.walk_start_x) * ease
            self.root.geometry(f"+{int(self.x)}+{int(self.y)}")
            
            if progress < 1.0:
                bob = abs(math.sin(self.frame * 0.4)) * 4
                move_parts(head_parts, 0, -bob)
                move_parts(ear_parts, 0, -bob * 0.7) 
                move_parts(body_parts, 0, -bob * 0.5)
                
                self.target_scale_x = 1.0 - bob*0.01
                self.target_scale_y = 1.0 + bob*0.01
                
                paw_speed = 0.8
                if (self.frame * paw_speed) % 8 < 4:
                    move_parts(paw_fl_parts, 0, -6)
                    move_parts(paw_br_parts, 0, -6)
                else:
                    move_parts(paw_fr_parts, 0, -6)
                    move_parts(paw_bl_parts, 0, -6)
                    
                tilt = -2 if self.direction < 0 else 2
                move_parts(head_parts, tilt, 0)
                move_parts(ear_parts, tilt, 0)
                
            if progress >= 1.0:
                self.state = "idle"
                
        elif self.state == "wobble":
            if self.frame % 4 < 2:
                self.target_wobble_x = -15
            else:
                self.target_wobble_x = 15
            dx = self.wobble_x
            self.canvas.move(self.parts["tail"], -dx*1.5, 0)
            move_parts(ear_parts, -dx*0.5, 2)
            
        elif self.state == "purr":
            dx = -1 if self.frame % 4 < 2 else 1
            move_parts(head_parts, dx, math.sin(self.frame*0.2)*1)
            move_parts(ear_parts, dx, math.sin(self.frame*0.2)*1)
            
        elif self.state == "scroll":
            self.canvas.create_rectangle(cx+10, cy+20, cx+25, cy+20 + self.frame*2, fill="white", outline="#999")
            if self.frame % 2 == 0:
                move_parts(paw_fl_parts, 0, 4)
                move_parts(paw_fr_parts, 0, -4)
            else:
                move_parts(paw_fl_parts, 0, -4)
                move_parts(paw_fr_parts, 0, 4)
                
        elif self.state == "hunt":
            move_parts(head_parts, 0, 6)
            move_parts(ear_parts, 0, 8) 
            self.target_scale_x = 1.1
            self.target_scale_y = 0.8
            
            wiggle_x = math.sin(self.frame * 1.5) * 4
            move_parts(body_parts, wiggle_x, 0)
            self.canvas.move(self.parts["tail"], wiggle_x * 1.5, 0)
            move_parts(paw_bl_parts, wiggle_x * 0.5, 0)
            move_parts(paw_br_parts, wiggle_x * 0.5, 0)
            
        elif self.state == "pounce":
            progress = self.frame / 20.0
            if progress <= 1.0:
                height = 50
                dy = -4 * height * progress * (1 - progress)
                
                self.x = self.pounce_start_x + (self.pounce_target_x - self.pounce_start_x) * progress
                self.y = self.pounce_start_y + (self.pounce_target_y - self.pounce_start_y) * progress
                self.root.geometry(f"+{int(self.x)}+{int(self.y)}")
                
                if progress < 0.2:
                    self.target_scale_x = 0.8
                    self.target_scale_y = 1.2
                elif progress > 0.8:
                    self.target_scale_x = 1.2
                    self.target_scale_y = 0.8
                    
                self.canvas.move("all", 0, dy)
            else:
                ground_y = self.root.winfo_screenheight() - self.height - 50
                if self.y < ground_y - 10:
                    self.state = "fall"
                    self.frame = 0
                    self.fall_start_y = self.y
                    self.fall_target_y = ground_y
                else:
                    self.state = "idle"
                    
        elif self.state == "fall":
            t = self.frame
            g = 3.0
            new_y = self.fall_start_y + 0.5 * g * (t**2)
            
            if new_y >= self.fall_target_y:
                self.y = self.fall_target_y
                self.root.geometry(f"+{int(self.x)}+{int(self.y)}")
                self.state = "idle"
                self.target_scale_x = 1.4
                self.target_scale_y = 0.6
                self.vel_scale_y = -0.15
            else:
                self.y = new_y
                self.root.geometry(f"+{int(self.x)}+{int(self.y)}")
                self.target_scale_x = 0.8
                self.target_scale_y = 1.3
                
                if self.frame % 4 < 2:
                    move_parts(paw_fl_parts, 0, -15)
                    move_parts(paw_fr_parts, 0, -10)
                else:
                    move_parts(paw_fl_parts, 0, -10)
                    move_parts(paw_fr_parts, 0, -15)
                    
        elif self.state == "sleep":
            t = (self.frame % 120) / 120.0
            breathe = math.sin(t * math.pi * 2)
            self.target_scale_x = 1.05 + breathe*0.02
            self.target_scale_y = 0.9 - breathe*0.02
            
            move_parts(head_parts, 0, 10 + breathe*2)
            move_parts(ear_parts, 0, 15 + breathe*2)
            move_parts(paw_fl_parts, 5, -5)
            move_parts(paw_fr_parts, -5, -5)

        mx = self.mouse_global_x - (self.x + cx)
        my = self.mouse_global_y - (self.y + cy)
        mdist = math.hypot(mx, my)
        
        target_px, target_py = 0, 0
        
        if self.state == "walk":
            target_px = 6 if self.direction > 0 else -6
            target_py = 0
        elif self.state in ["stretch", "eat", "jump"]:
            target_px, target_py = 0, 0
        elif mdist > 0:
            target_px = (mx / mdist) * 4
            target_py = (my / mdist) * 4
            
        self.parallax_x += (target_px - self.parallax_x) * 0.2
        self.parallax_y += (target_py - self.parallax_y) * 0.2
        
        move_parts(face_parts, self.parallax_x, self.parallax_y)
        move_parts(head_base, self.parallax_x * 0.3, self.parallax_y * 0.3)
        move_parts(ear_parts, -self.parallax_x * 0.3, -self.parallax_y * 0.3)

        self.scale_x, self.vel_scale_x = apply_spring(self.scale_x, self.vel_scale_x, self.target_scale_x, tension=0.25, dampening=0.65)
        self.scale_y, self.vel_scale_y = apply_spring(self.scale_y, self.vel_scale_y, self.target_scale_y, tension=0.25, dampening=0.65)
        
        self.wobble_x, self.vel_wobble_x = apply_spring(self.wobble_x, self.vel_wobble_x, self.target_wobble_x, tension=0.2, dampening=0.7)
        
        if abs(self.wobble_x) > 0.1:
            move_parts(head_parts, self.wobble_x, 0)
        
        if abs(self.scale_x - 1.0) > 0.001 or abs(self.scale_y - 1.0) > 0.001:
            self.canvas.scale("all", cx, cy+25, self.scale_x, self.scale_y)

        self.root.after(30, self.update_loop)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = DeskCat()
    app.run()
