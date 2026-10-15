# 🐾 DeskCat (Comnyang)

> Your adorable, animated desktop pet companion for Windows that reacts to typing, mouse interactions, file drops, and external AI agents!

DeskCat is a transparent, frameless, always-on-top desktop companion designed to sit on your screen and keep you company while you work or code.

---

## ✨ Features

- **🐾 Keyboard Kneading (Bongo Style)**: Alternates left and right front paws whenever you type on your keyboard.
- **🔥 Overheat Mode**: Typing at speeds exceeding 80 WPM turns the cat red with rising steam bubbles!
- **👀 Global Cursor Tracking & Parallax**: Eyes and face layers smoothly follow your cursor wherever it moves across all monitors.
- **😻 Petting & Purring**: Hover your cursor over the cat's head to trigger rapid purring vibrations, happy arched eyes, and blushing cheeks.
- **🎯 Hunting & Pouncing**: Moving your mouse rapidly across the screen puts the cat into "hunt mode" (butt wiggle and dilated pupils), followed by a dynamic pounce across the desktop with spring physics and gravity bounce.
- **🍡 Mochi Stretching & Wobble**: Click and drag to stretch the cat like mochi. Rapid shaking triggers a spring wobble effect.
- **📄 File Eating**: Drag and drop any file directly onto the cat to trigger an animated document shredding / eating sequence.
- **📌 Pinned Notes**: Right-click the cat to pin a sticky note memo right beside it.
- **🤖 AI Agent Webhooks**: Built-in HTTP server listening on port `3000`:
  - `POST /api/status` with `{"status": "thinking"}` or `{"status": "done"}` (triggers thinking eyes or celebration jumps).
  - `POST /api/message` with `{"message": "Hello!"}` (displays a floating speech bubble).
- **🖥️ Smart Fullscreen Hiding**: Automatically detects fullscreen games, videos, or apps using Win32 API and hides temporarily so it never obstructs your view.
- **🚀 Windows Startup Support**: Toggle auto-start with Windows via the context menu.

---

## 🎨 Themes & Customization

Right-click the cat to choose from preset color themes:
- **Orange & White**
- **Midnight Black**
- **Gray Tabby**
- **Siamese**

Appearance settings are saved persistently in `config.json`.

---

## 🚀 Getting Started

### ⚡ Quick Start (Windows Standalone .exe - No Setup Required)

The fastest way to get DeskCat on your computer:

1. **Download**:
   - [**⬇️ Download deskcat.exe (Direct Download)**](https://github.com/Rudra512004/deskcat/raw/main/release/deskcat.exe)
   - Or browse [GitHub Releases](https://github.com/Rudra512004/deskcat/releases)
2. **Install & Run**:
   - Save `deskcat.exe` anywhere on your computer (e.g. `Downloads`, `Desktop`, or a custom folder).
   - Double-click `deskcat.exe` to launch immediately!
   - *(Optional)* Right-click the cat and select **"Toggle Start with Windows"** to have DeskCat automatically launch on system startup.

---

### Option 2: Run from Python Source

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Rudra512004/deskcat.git
   cd deskcat
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run DeskCat**:
   ```bash
   python deskcat.py
   ```

5. **Build Standalone Windows Executable**:
   ```bash
   pyinstaller deskcat.spec
   ```
   The standalone executable will be located in `dist/deskcat.exe`.

---

### Option 3: Electron Version

An alternative web-technologies implementation (HTML5 / CSS / uiohook) is also included:

1. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

2. **Start the Electron app**:
   ```bash
   npm start
   ```

---

## 🔌 AI Agent Integration API

DeskCat exposes a lightweight local HTTP server on `http://localhost:3000` to hook into AI agents (e.g. Gemini, Claude, Cursor, LangChain):

```bash
# Set status to thinking
curl -X POST http://localhost:3000/api/status -H "Content-Type: application/json" -d "{\"status\":\"thinking\"}"

# Set status to done (triggers celebration jump)
curl -X POST http://localhost:3000/api/status -H "Content-Type: application/json" -d "{\"status\":\"done\"}"

# Show a speech bubble message
curl -X POST http://localhost:3000/api/message -H "Content-Type: application/json" -d "{\"message\":\"Task completed! Meow!\"}"
```

---

## 📁 Project Structure

```
deskcat/
├── deskcat.py          # Native Python/Tkinter application with custom vector animations
├── input_hook.py       # Global mouse & keyboard input capture (pynput)
├── api_server.py       # Flask REST API server for AI agent webhooks
├── config.json         # Appearance configuration
├── deskcat.spec        # PyInstaller build specification
├── requirements.txt    # Python dependencies
├── main.js             # Electron main process & Express server
├── preload.js          # Electron IPC context bridge
├── renderer.js         # Electron DOM animations & input listeners
├── index.html          # Electron UI layout
├── styles.css          # CSS animations (breathe, purr, jump, overheat)
└── package.json        # Node.js dependencies
```

---

## 📜 License

MIT License.
