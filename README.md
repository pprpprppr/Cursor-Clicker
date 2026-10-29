# 🖱️ AutoCursor Pro — Mouse Cursor Clicker

**AutoCursor Pro** is a modern, feature-rich mouse cursor auto-clicker app designed for Linux (X11) and cross-platform desktop environments. It allows you to specify exact screen coordinates or dynamically follow the mouse cursor, and trigger clicks periodically with precision intervals.

---

## ✨ Features

- **🎯 Coordinate Targeting**:
  - **Fixed Screen Coordinate**: Enter exact `X` and `Y` pixel coordinates.
  - **📍 Interactive Location Picker**: 3-second live countdown with real-time cursor coordinate tracking to lock onto any button or UI element on screen.
  - **📌 Instant Capture Hotkey (`F7`)**: Press `F7` at any time, anywhere on screen to instantly lock in the current mouse cursor location.
  - **Dynamic Cursor Mode**: Option to click wherever the mouse is actively hovering.
- **⏱️ Precision Periodic Interval**:
  - Configurable in **Hours**, **Minutes**, **Seconds**, and **Milliseconds** (down to 5 ms).
  - **Random Jitter (Anti-Detection)**: Optional `± ms` random variation for natural, human-like clicking cadence.
- **👆 Click Options**:
  - Mouse button: **Left**, **Right**, or **Middle**.
  - Click type: **Single**, **Double**, or **Triple** click.
  - Repeat mode: Repeat continuously until stopped, or stop after a fixed click count.
  - **Return Cursor to Origin**: Automatically returns cursor to where you were working after each background click.
- **⚡ Global Hotkeys & Safety**:
  - `F6`: Start / Stop clicking at any time (even when the app window is minimized or unfocused).
  - `F7`: Instantly capture current cursor position as target coordinates.
  - **Hardware Fail-Safe**: Move mouse cursor to any corner of the screen to trigger an immediate emergency halt.
  - **Pin on Top 📌**: Keeps the control window floating above your target apps/games.
- **💻 CLI & GUI Modes**: Launch the modern dark-themed GUI or run headlessly via terminal commands.

---

## 🚀 Quick Start

### 1. Launch GUI (Desktop App)

Run with the launcher script:
```bash
./run.sh
```
Or directly with Python:
```bash
python3 main.py
```

### 2. How to Set Target Location and Start Clicking

1. **Option A (Instant Hotkey)**: Move your mouse to the spot on your screen you want to click and press **`F7`**. The coordinates will automatically lock into the app.
2. **Option B (Countdown Picker)**: Click **"📍 Pick Location"**. You will have 3 seconds to move your mouse to the target spot. The app locks the coordinates when the countdown finishes.
3. **Option C (Manual Entry)**: Type the exact `X` and `Y` pixel coordinates.
4. Set your desired **Interval** (e.g., `1` second or `250` ms).
5. Press **`F6`** (or click the green **START** button) to begin clicking.
6. Press **`F6`** again (or click **STOP**) whenever you want to pause.

---

## ⌨️ Global Shortcuts & Emergency Stop

When an auto-clicker is clicking rapidly, moving the mouse can be difficult. Use these global keyboard shortcuts to control it without touching the mouse:

| Shortcut | Action | Description |
| :--- | :--- | :--- |
| **`ESC`** | **🛑 Instant Emergency Stop** | Immediately aborts clicking and releases mouse control back to you |
| **`F6`** | **Start / Stop Toggle** | Starts clicking or stops active clicking |
| **`F8`** | **Secondary Stop** | Instant stop alternative (useful on laptops without dedicated F-keys) |
| **`F7`** | **Capture Cursor Location** | Saves the cursor's current `(X, Y)` position as the target coordinate |
| **Corner of Screen** | **Hardware Fail-Safe** | Move mouse to any corner of the display to abort |

> [!TIP]
> You can also customize the emergency stop key in the GUI under **"4. Emergency Stop & Shortcuts"** (choose from `ESC`, `F6`, `F8`, `F10`, or `PAUSE`).

---

## 🖥️ Command Line (CLI) Usage

AutoCursor Pro also supports running directly from the terminal without the GUI:

```bash
# Click at coordinates (500, 300) every 0.5 seconds, 20 times:
python3 main.py --x 500 --y 300 --interval 0.5 --count 20

# Interactively pick location with Enter, then click every 2 seconds:
python3 main.py --pick --interval 2.0

# Click wherever cursor is hovering every 100ms with jitter:
python3 main.py --cursor --interval 0.1 --jitter 0.02

# Right-click at (1200, 800) double-click:
python3 main.py --x 1200 --y 800 --button right --type double

# View all CLI options:
python3 main.py --help
```

---

## 📁 Project Structure

```
agtplay/
├── autoclicker/
│   ├── __init__.py
│   ├── engine.py          # High-precision threaded clicking engine
│   ├── hotkeys.py         # Global keyboard listeners (F6/F7)
│   ├── ui.py              # Tkinter dark-themed interface
│   └── cli.py             # Headless command-line mode
├── main.py                # Main application entry point
├── run.sh                 # Executable launcher script
├── autocursor.desktop     # Desktop application shortcut
├── test_clicker.py        # Automated test suite
├── requirements.txt       # Python dependencies
└── README.md              # Documentation
```

---

## 🧪 Testing

Run unit & integration tests:
```bash
python3 -m unittest test_clicker.py
```
All tests verify thread lifecycle, click counts, coordinates, hotkeys, and UI startup.
