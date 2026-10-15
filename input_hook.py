import threading
import queue
from pynput import mouse, keyboard
import time

class InputHook:
    def __init__(self):
        self.event_queue = queue.Queue()
        self.mouse_listener = None
        self.keyboard_listener = None
        self.key_press_times = []

    def start(self):
        self.mouse_listener = mouse.Listener(
            on_move=self.on_move,
            on_scroll=self.on_scroll
        )
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_press
        )
        self.mouse_listener.start()
        self.keyboard_listener.start()

    def stop(self):
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()

    def on_move(self, x, y):
        self.event_queue.put({'type': 'mouse_move', 'x': x, 'y': y})

    def on_scroll(self, x, y, dx, dy):
        self.event_queue.put({'type': 'mouse_scroll', 'dx': dx, 'dy': dy})

    def on_press(self, key):
        now = time.time()
        self.key_press_times.append(now)
        # Clean up old presses (> 10s old)
        self.key_press_times = [t for t in self.key_press_times if now - t < 10]
        
        # Calculate WPM approximation
        # WPM = (presses / 5 chars per word) * (60s / 10s window) = presses * 1.2
        wpm = len(self.key_press_times) * 1.2
        
        self.event_queue.put({'type': 'key_press', 'wpm': wpm})
