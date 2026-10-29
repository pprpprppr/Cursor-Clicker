"""Tkinter Graphical User Interface for Mouse Cursor Clicker.

Features:
- Instant Emergency Stop Shortcut (ESC / F6 / F8) to immediately free the mouse
- Fixed screen coordinate picking (with countdown or immediate hotkey)
- Live cursor position tracking
- Configurable interval (Hours, Minutes, Seconds, Milliseconds)
- Random jitter option
- Left / Right / Middle mouse buttons and Single / Double / Triple clicks
- Repeat count (infinite or fixed)
- Restore cursor to original position option
- Global Hotkeys (ESC to emergency stop, F6 to toggle, F7 to capture position)
- PyAutoGUI Fail-Safe protection
- Clean, modern dark theme
"""

import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui

from autoclicker.engine import ClickerEngine, ClickConfig
from autoclicker.hotkeys import HotkeyManager


class ModernAutoClickerUI:
    """Modern Dark Themed UI for Mouse Clicker."""

    # Color palette
    BG_DARK = "#161922"
    BG_CARD = "#212634"
    BG_CARD_ALT = "#293042"
    BORDER_COLOR = "#343c53"
    ACCENT_CYAN = "#00b4d8"
    ACCENT_GREEN = "#06d6a0"
    ACCENT_RED = "#ef476f"
    ACCENT_ORANGE = "#ffd166"
    TEXT_MAIN = "#ffffff"
    TEXT_MUTED = "#9ba3b5"
    INPUT_BG = "#13161f"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AutoCursor Pro — Mouse Clicker")
        self.root.geometry("540x800")
        self.root.minsize(500, 720)
        self.root.configure(bg=self.BG_DARK)

        # PyAutoGUI screen bounds
        self.screen_width, self.screen_height = pyautogui.size()

        # Engine
        self.engine = ClickerEngine()

        # Global Hotkey manager with dedicated emergency stop callback
        self.var_stop_key = tk.StringVar(value="ESC")
        self.hotkeys = HotkeyManager(
            on_toggle=self._safe_hotkey_toggle,
            on_stop=self._safe_hotkey_stop,
            on_capture_pos=self._safe_hotkey_capture,
            is_active_check=lambda: self.engine.is_running,
            selected_stop_key=self.var_stop_key.get(),
        )

        # Engine callbacks
        self.engine.on_start = lambda: self.root.after(0, self._on_engine_start)
        self.engine.on_stop = lambda count: self.root.after(0, self._on_engine_stop, count)
        self.engine.on_click = lambda count: self.root.after(0, self._on_engine_click, count)
        self.engine.on_error = lambda err: self.root.after(0, self._on_engine_error, err)

        # Internal state
        self.picking_countdown_active = False

        # Configure styles
        self._setup_styles()

        # Build interface
        self._build_ui()

        # Local window hotkey fallbacks
        self.root.bind("<Escape>", lambda e: self._stop_clicker())
        self.root.bind("<F6>", lambda e: self._toggle_clicker())

        # Start background listeners and tracking
        self.hotkeys.start()
        self._schedule_cursor_tracker()

        # Clean close protocol
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_styles(self):
        """Configure ttk styles for dark theme."""
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Basic defaults
        self.style.configure(".", background=self.BG_DARK, foreground=self.TEXT_MAIN, font=("Sans", 10))

        # Frames
        self.style.configure("Card.TFrame", background=self.BG_CARD, relief="flat")

        # Labels
        self.style.configure("Header.TLabel", font=("Sans", 14, "bold"), foreground=self.TEXT_MAIN, background=self.BG_DARK)
        self.style.configure("SubHeader.TLabel", font=("Sans", 9), foreground=self.TEXT_MUTED, background=self.BG_DARK)
        self.style.configure("CardTitle.TLabel", font=("Sans", 11, "bold"), foreground=self.ACCENT_CYAN, background=self.BG_CARD)
        self.style.configure("CardText.TLabel", font=("Sans", 10), foreground=self.TEXT_MAIN, background=self.BG_CARD)
        self.style.configure("Muted.TLabel", font=("Sans", 9), foreground=self.TEXT_MUTED, background=self.BG_CARD)

        # Radio & Check buttons
        self.style.configure(
            "Card.TRadiobutton",
            background=self.BG_CARD,
            foreground=self.TEXT_MAIN,
            font=("Sans", 10),
            focuscolor=self.BG_CARD,
        )
        self.style.map("Card.TRadiobutton", background=[("active", self.BG_CARD)])

        self.style.configure(
            "Card.TCheckbutton",
            background=self.BG_CARD,
            foreground=self.TEXT_MAIN,
            font=("Sans", 10),
            focuscolor=self.BG_CARD,
        )
        self.style.map("Card.TCheckbutton", background=[("active", self.BG_CARD)])

        # Action Buttons
        self.style.configure(
            "Primary.TButton",
            font=("Sans", 10, "bold"),
            background=self.ACCENT_CYAN,
            foreground="#000000",
            borderwidth=0,
            padding=6,
        )
        self.style.map(
            "Primary.TButton",
            background=[("active", "#38c3e8"), ("pressed", "#0096c7")],
        )

        self.style.configure(
            "Secondary.TButton",
            font=("Sans", 9),
            background=self.BG_CARD_ALT,
            foreground=self.TEXT_MAIN,
            borderwidth=0,
            padding=5,
        )
        self.style.map(
            "Secondary.TButton",
            background=[("active", "#343c53"), ("pressed", "#212634")],
        )

    def _build_ui(self):
        """Construct the UI layout."""
        # Top Header Bar
        header_frame = tk.Frame(self.root, bg=self.BG_DARK)
        header_frame.pack(fill=tk.X, padx=16, pady=(12, 6))

        title_col = tk.Frame(header_frame, bg=self.BG_DARK)
        title_col.pack(side=tk.LEFT)

        ttk.Label(title_col, text="🖱️ AutoCursor Pro", style="Header.TLabel").pack(anchor="w")
        ttk.Label(title_col, text=f"Display: {self.screen_width} × {self.screen_height} | Global Hotkeys Active", style="SubHeader.TLabel").pack(anchor="w")

        # Top Controls: Always on Top toggle
        self.var_always_on_top = tk.BooleanVar(value=True)
        self.root.attributes("-topmost", True)
        top_check = tk.Checkbutton(
            header_frame,
            text="Pin on Top 📌",
            variable=self.var_always_on_top,
            command=self._toggle_always_on_top,
            bg=self.BG_DARK,
            fg=self.TEXT_MUTED,
            selectcolor=self.INPUT_BG,
            activebackground=self.BG_DARK,
            activeforeground=self.TEXT_MAIN,
            font=("Sans", 9),
            relief="flat",
            bd=0,
            highlightthickness=0,
        )
        top_check.pack(side=tk.RIGHT, pady=2)

        # Emergency Stop Banner (Prominent indicator)
        emergency_banner = tk.Frame(self.root, bg="#2d1217", padx=12, pady=6, bd=1, relief="ridge")
        emergency_banner.pack(fill=tk.X, padx=12, pady=(0, 6))

        tk.Label(
            emergency_banner,
            text="🛑 EMERGENCY STOP SHORTCUT:",
            bg="#2d1217",
            fg=self.ACCENT_RED,
            font=("Sans", 9, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.lbl_stop_notice = tk.Label(
            emergency_banner,
            text="Press [ESC] or [F6] anywhere to immediately stop and free mouse",
            bg="#2d1217",
            fg=self.TEXT_MAIN,
            font=("Sans", 9),
        )
        self.lbl_stop_notice.pack(side=tk.LEFT)

        # Scrollable container for main content
        canvas = tk.Canvas(self.root, bg=self.BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        self.content_frame = tk.Frame(canvas, bg=self.BG_DARK)

        self.content_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self.content_frame, anchor="nw", width=520)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=2)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Build Cards
        self._build_location_card(self.content_frame)
        self._build_interval_card(self.content_frame)
        self._build_options_card(self.content_frame)
        self._build_shortcuts_card(self.content_frame)
        self._build_controls_card(self.content_frame)

        # Footer Status bar
        self._build_footer(self.root)

    def _build_location_card(self, parent):
        """Card for target coordinates setting."""
        card = tk.LabelFrame(
            parent,
            text="  1. Target Location  ",
            bg=self.BG_CARD,
            fg=self.ACCENT_CYAN,
            font=("Sans", 10, "bold"),
            relief="groove",
            bd=1,
            padx=12,
            pady=10,
        )
        card.pack(fill=tk.X, pady=6)

        # Mode Selection
        self.var_loc_mode = tk.StringVar(value="fixed")

        mode_row = tk.Frame(card, bg=self.BG_CARD)
        mode_row.pack(fill=tk.X, pady=(0, 8))

        rb1 = tk.Radiobutton(
            mode_row,
            text="Fixed Screen Location",
            variable=self.var_loc_mode,
            value="fixed",
            command=self._on_loc_mode_change,
            bg=self.BG_CARD,
            fg=self.TEXT_MAIN,
            selectcolor=self.INPUT_BG,
            activebackground=self.BG_CARD,
            activeforeground=self.TEXT_MAIN,
            font=("Sans", 10),
            bd=0,
            highlightthickness=0,
        )
        rb1.pack(side=tk.LEFT, padx=(0, 16))

        rb2 = tk.Radiobutton(
            mode_row,
            text="Follow Mouse Cursor",
            variable=self.var_loc_mode,
            value="cursor",
            command=self._on_loc_mode_change,
            bg=self.BG_CARD,
            fg=self.TEXT_MAIN,
            selectcolor=self.INPUT_BG,
            activebackground=self.BG_CARD,
            activeforeground=self.TEXT_MAIN,
            font=("Sans", 10),
            bd=0,
            highlightthickness=0,
        )
        rb2.pack(side=tk.LEFT)

        # Coordinates Row
        self.coords_frame = tk.Frame(card, bg=self.BG_CARD)
        self.coords_frame.pack(fill=tk.X, pady=4)

        # Initial default: center of screen
        default_x = self.screen_width // 2
        default_y = self.screen_height // 2

        tk.Label(self.coords_frame, text="X:", bg=self.BG_CARD, fg=self.TEXT_MUTED, font=("Sans", 10, "bold")).pack(side=tk.LEFT, padx=(0, 4))
        self.entry_x = tk.Spinbox(
            self.coords_frame,
            from_=0,
            to=self.screen_width,
            width=6,
            bg=self.INPUT_BG,
            fg=self.TEXT_MAIN,
            insertbackground=self.TEXT_MAIN,
            font=("Sans", 10),
            relief="flat",
            bd=3,
        )
        self.entry_x.delete(0, tk.END)
        self.entry_x.insert(0, str(default_x))
        self.entry_x.pack(side=tk.LEFT, padx=(0, 14))

        tk.Label(self.coords_frame, text="Y:", bg=self.BG_CARD, fg=self.TEXT_MUTED, font=("Sans", 10, "bold")).pack(side=tk.LEFT, padx=(0, 4))
        self.entry_y = tk.Spinbox(
            self.coords_frame,
            from_=0,
            to=self.screen_height,
            width=6,
            bg=self.INPUT_BG,
            fg=self.TEXT_MAIN,
            insertbackground=self.TEXT_MAIN,
            font=("Sans", 10),
            relief="flat",
            bd=3,
        )
        self.entry_y.delete(0, tk.END)
        self.entry_y.insert(0, str(default_y))
        self.entry_y.pack(side=tk.LEFT, padx=(0, 16))

        # Pick Button
        self.btn_pick = tk.Button(
            self.coords_frame,
            text="📍 Pick Location",
            command=self._start_pick_countdown,
            bg=self.ACCENT_CYAN,
            fg="#000000",
            activebackground="#38c3e8",
            font=("Sans", 9, "bold"),
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
        )
        self.btn_pick.pack(side=tk.LEFT, padx=(0, 8))

        # Capture Now button
        self.btn_capture = tk.Button(
            self.coords_frame,
            text="📌 Capture (F7)",
            command=self._capture_current_cursor,
            bg=self.BG_CARD_ALT,
            fg=self.TEXT_MAIN,
            activebackground=self.BORDER_COLOR,
            activeforeground=self.TEXT_MAIN,
            font=("Sans", 9),
            relief="flat",
            padx=8,
            pady=4,
            cursor="hand2",
        )
        self.btn_capture.pack(side=tk.LEFT)

        # Status row for coordinates
        self.lbl_coord_status = tk.Label(
            card,
            text=f"Live Cursor: (X: {default_x}, Y: {default_y}) | Press F7 anywhere to lock current cursor position",
            bg=self.BG_CARD,
            fg=self.TEXT_MUTED,
            font=("Sans", 8),
            anchor="w",
        )
        self.lbl_coord_status.pack(fill=tk.X, pady=(6, 0))

    def _build_interval_card(self, parent):
        """Card for click interval and rate."""
        card = tk.LabelFrame(
            parent,
            text="  2. Click Interval  ",
            bg=self.BG_CARD,
            fg=self.ACCENT_CYAN,
            font=("Sans", 10, "bold"),
            relief="groove",
            bd=1,
            padx=12,
            pady=10,
        )
        card.pack(fill=tk.X, pady=6)

        spin_row = tk.Frame(card, bg=self.BG_CARD)
        spin_row.pack(fill=tk.X, pady=4)

        # Hours
        tk.Label(spin_row, text="Hours:", bg=self.BG_CARD, fg=self.TEXT_MUTED, font=("Sans", 9)).pack(side=tk.LEFT)
        self.spin_hours = tk.Spinbox(spin_row, from_=0, to=999, width=3, bg=self.INPUT_BG, fg=self.TEXT_MAIN, insertbackground=self.TEXT_MAIN, relief="flat", bd=3)
        self.spin_hours.delete(0, tk.END)
        self.spin_hours.insert(0, "0")
        self.spin_hours.pack(side=tk.LEFT, padx=(2, 10))

        # Minutes
        tk.Label(spin_row, text="Mins:", bg=self.BG_CARD, fg=self.TEXT_MUTED, font=("Sans", 9)).pack(side=tk.LEFT)
        self.spin_mins = tk.Spinbox(spin_row, from_=0, to=59, width=3, bg=self.INPUT_BG, fg=self.TEXT_MAIN, insertbackground=self.TEXT_MAIN, relief="flat", bd=3)
        self.spin_mins.delete(0, tk.END)
        self.spin_mins.insert(0, "0")
        self.spin_mins.pack(side=tk.LEFT, padx=(2, 10))

        # Seconds
        tk.Label(spin_row, text="Secs:", bg=self.BG_CARD, fg=self.TEXT_MUTED, font=("Sans", 9)).pack(side=tk.LEFT)
        self.spin_secs = tk.Spinbox(spin_row, from_=0, to=59, width=3, bg=self.INPUT_BG, fg=self.TEXT_MAIN, insertbackground=self.TEXT_MAIN, relief="flat", bd=3)
        self.spin_secs.delete(0, tk.END)
        self.spin_secs.insert(0, "1")
        self.spin_secs.pack(side=tk.LEFT, padx=(2, 10))

        # Milliseconds
        tk.Label(spin_row, text="Ms:", bg=self.BG_CARD, fg=self.TEXT_MUTED, font=("Sans", 9)).pack(side=tk.LEFT)
        self.spin_ms = tk.Spinbox(spin_row, from_=0, to=999, width=4, bg=self.INPUT_BG, fg=self.TEXT_MAIN, insertbackground=self.TEXT_MAIN, relief="flat", bd=3)
        self.spin_ms.delete(0, tk.END)
        self.spin_ms.insert(0, "0")
        self.spin_ms.pack(side=tk.LEFT, padx=(2, 10))

        # Jitter options row
        jitter_row = tk.Frame(card, bg=self.BG_CARD)
        jitter_row.pack(fill=tk.X, pady=(8, 2))

        self.var_jitter_enabled = tk.BooleanVar(value=False)
        cb_jitter = tk.Checkbutton(
            jitter_row,
            text="Random Jitter (Anti-detection)",
            variable=self.var_jitter_enabled,
            bg=self.BG_CARD,
            fg=self.TEXT_MAIN,
            selectcolor=self.INPUT_BG,
            activebackground=self.BG_CARD,
            activeforeground=self.TEXT_MAIN,
            font=("Sans", 9),
            bd=0,
            highlightthickness=0,
        )
        cb_jitter.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(jitter_row, text="± ms:", bg=self.BG_CARD, fg=self.TEXT_MUTED, font=("Sans", 9)).pack(side=tk.LEFT)
        self.spin_jitter_ms = tk.Spinbox(jitter_row, from_=10, to=5000, width=5, bg=self.INPUT_BG, fg=self.TEXT_MAIN, insertbackground=self.TEXT_MAIN, relief="flat", bd=3)
        self.spin_jitter_ms.delete(0, tk.END)
        self.spin_jitter_ms.insert(0, "50")
        self.spin_jitter_ms.pack(side=tk.LEFT, padx=(4, 0))

    def _build_options_card(self, parent):
        """Card for Mouse Button, Click Type, and Repeat Counts."""
        card = tk.LabelFrame(
            parent,
            text="  3. Click Settings & Repeat  ",
            bg=self.BG_CARD,
            fg=self.ACCENT_CYAN,
            font=("Sans", 10, "bold"),
            relief="groove",
            bd=1,
            padx=12,
            pady=10,
        )
        card.pack(fill=tk.X, pady=6)

        # Mouse Button & Click Type
        settings_row = tk.Frame(card, bg=self.BG_CARD)
        settings_row.pack(fill=tk.X, pady=2)

        tk.Label(settings_row, text="Mouse Button:", bg=self.BG_CARD, fg=self.TEXT_MUTED, font=("Sans", 9)).pack(side=tk.LEFT, padx=(0, 4))
        self.var_button = tk.StringVar(value="left")
        btn_combo = ttk.Combobox(
            settings_row,
            textvariable=self.var_button,
            values=["left", "right", "middle"],
            width=7,
            state="readonly",
        )
        btn_combo.pack(side=tk.LEFT, padx=(0, 16))

        tk.Label(settings_row, text="Click Type:", bg=self.BG_CARD, fg=self.TEXT_MUTED, font=("Sans", 9)).pack(side=tk.LEFT, padx=(0, 4))
        self.var_click_type = tk.StringVar(value="single")
        type_combo = ttk.Combobox(
            settings_row,
            textvariable=self.var_click_type,
            values=["single", "double", "triple"],
            width=7,
            state="readonly",
        )
        type_combo.pack(side=tk.LEFT)

        # Repeat Count
        repeat_row = tk.Frame(card, bg=self.BG_CARD)
        repeat_row.pack(fill=tk.X, pady=(10, 4))

        self.var_repeat_mode = tk.StringVar(value="infinite")
        rb_inf = tk.Radiobutton(
            repeat_row,
            text="Repeat until stopped",
            variable=self.var_repeat_mode,
            value="infinite",
            bg=self.BG_CARD,
            fg=self.TEXT_MAIN,
            selectcolor=self.INPUT_BG,
            activebackground=self.BG_CARD,
            activeforeground=self.TEXT_MAIN,
            font=("Sans", 9),
            bd=0,
            highlightthickness=0,
        )
        rb_inf.pack(side=tk.LEFT, padx=(0, 12))

        rb_count = tk.Radiobutton(
            repeat_row,
            text="Repeat count:",
            variable=self.var_repeat_mode,
            value="count",
            bg=self.BG_CARD,
            fg=self.TEXT_MAIN,
            selectcolor=self.INPUT_BG,
            activebackground=self.BG_CARD,
            activeforeground=self.TEXT_MAIN,
            font=("Sans", 9),
            bd=0,
            highlightthickness=0,
        )
        rb_count.pack(side=tk.LEFT, padx=(0, 4))

        self.spin_repeat_count = tk.Spinbox(
            repeat_row,
            from_=1,
            to=999999,
            width=6,
            bg=self.INPUT_BG,
            fg=self.TEXT_MAIN,
            insertbackground=self.TEXT_MAIN,
            relief="flat",
            bd=3,
        )
        self.spin_repeat_count.delete(0, tk.END)
        self.spin_repeat_count.insert(0, "100")
        self.spin_repeat_count.pack(side=tk.LEFT, padx=(0, 4))

        # Restore Cursor Option
        restore_row = tk.Frame(card, bg=self.BG_CARD)
        restore_row.pack(fill=tk.X, pady=(6, 2))

        self.var_restore_cursor = tk.BooleanVar(value=False)
        cb_restore = tk.Checkbutton(
            restore_row,
            text="Return mouse cursor to original position after click",
            variable=self.var_restore_cursor,
            bg=self.BG_CARD,
            fg=self.TEXT_MUTED,
            selectcolor=self.INPUT_BG,
            activebackground=self.BG_CARD,
            activeforeground=self.TEXT_MAIN,
            font=("Sans", 9),
            bd=0,
            highlightthickness=0,
        )
        cb_restore.pack(side=tk.LEFT)

    def _build_shortcuts_card(self, parent):
        """Card for configuring shortcuts and emergency stop keys."""
        card = tk.LabelFrame(
            parent,
            text="  4. Emergency Stop & Shortcuts  ",
            bg=self.BG_CARD,
            fg=self.ACCENT_ORANGE,
            font=("Sans", 10, "bold"),
            relief="groove",
            bd=1,
            padx=12,
            pady=10,
        )
        card.pack(fill=tk.X, pady=6)

        row1 = tk.Frame(card, bg=self.BG_CARD)
        row1.pack(fill=tk.X, pady=2)

        tk.Label(row1, text="Emergency Stop Key:", bg=self.BG_CARD, fg=self.TEXT_MAIN, font=("Sans", 9, "bold")).pack(side=tk.LEFT, padx=(0, 8))

        stop_combo = ttk.Combobox(
            row1,
            textvariable=self.var_stop_key,
            values=["ESC", "F6", "F8", "F10", "PAUSE"],
            width=8,
            state="readonly",
        )
        stop_combo.pack(side=tk.LEFT, padx=(0, 12))
        stop_combo.bind("<<ComboboxSelected>>", self._on_stop_key_changed)

        tk.Label(
            row1,
            text="💡 ESC & F6 both stop clicking instantly",
            bg=self.BG_CARD,
            fg=self.TEXT_MUTED,
            font=("Sans", 9),
        ).pack(side=tk.LEFT)

        info_lbl = tk.Label(
            card,
            text="Whenever autoclicking is active, pressing the Stop Key releases cursor control immediately.",
            bg=self.BG_CARD,
            fg=self.TEXT_MUTED,
            font=("Sans", 8),
            anchor="w",
        )
        info_lbl.pack(fill=tk.X, pady=(4, 0))

    def _build_controls_card(self, parent):
        """Card for Start/Stop Button, Dedicated Emergency Stop Button, and Live Stats."""
        card = tk.Frame(parent, bg=self.BG_CARD, bd=1, relief="groove", padx=14, pady=12)
        card.pack(fill=tk.X, pady=8)

        # Buttons row
        btn_row = tk.Frame(card, bg=self.BG_CARD)
        btn_row.pack(fill=tk.X, pady=(0, 10))

        # Main Start / Stop Button
        self.btn_toggle = tk.Button(
            btn_row,
            text="▶  START CLICKER  (F6)",
            command=self._toggle_clicker,
            bg=self.ACCENT_GREEN,
            fg="#0f172a",
            activebackground="#10b981",
            activeforeground="#ffffff",
            font=("Sans", 12, "bold"),
            relief="flat",
            cursor="hand2",
            pady=10,
        )
        self.btn_toggle.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        # Dedicated Emergency Stop Button
        self.btn_emergency_stop = tk.Button(
            btn_row,
            text="🛑 STOP (ESC)",
            command=self._stop_clicker,
            bg="#b91c1c",
            fg="#ffffff",
            activebackground="#dc2626",
            activeforeground="#ffffff",
            font=("Sans", 11, "bold"),
            relief="flat",
            cursor="hand2",
            pady=10,
            padx=16,
        )
        self.btn_emergency_stop.pack(side=tk.RIGHT)

        # Stats display
        stats_frame = tk.Frame(card, bg=self.BG_CARD)
        stats_frame.pack(fill=tk.X)

        self.lbl_status_badge = tk.Label(
            stats_frame,
            text="● STOPPED",
            bg=self.BG_CARD,
            fg=self.ACCENT_RED,
            font=("Sans", 11, "bold"),
        )
        self.lbl_status_badge.pack(side=tk.LEFT)

        self.lbl_clicks_count = tk.Label(
            stats_frame,
            text="Clicks: 0",
            bg=self.BG_CARD,
            fg=self.TEXT_MAIN,
            font=("Sans", 11, "bold"),
        )
        self.lbl_clicks_count.pack(side=tk.RIGHT)

    def _build_footer(self, parent):
        """Bottom bar showing shortcuts and safety info."""
        footer = tk.Frame(parent, bg="#0d1117", padx=14, pady=8)
        footer.pack(side=tk.BOTTOM, fill=tk.X)

        shortcuts_text = "⚡ Press [ESC] or [F6] at any time to STOP  •  [F7] Capture Cursor  •  Fail-Safe: Move cursor to screen corner"
        tk.Label(
            footer,
            text=shortcuts_text,
            bg="#0d1117",
            fg=self.ACCENT_ORANGE,
            font=("Sans", 9, "bold"),
        ).pack(side=tk.LEFT)

    def _on_stop_key_changed(self, event=None):
        """Update hotkey manager when stop key selection changes."""
        key = self.var_stop_key.get()
        self.hotkeys.set_stop_key(key)
        self.lbl_stop_notice.config(
            text=f"Press [{key}] or [ESC] anywhere to immediately stop and free mouse"
        )
        self.btn_emergency_stop.config(text=f"🛑 STOP ({key})")

    def _on_loc_mode_change(self):
        """Handle toggling between fixed and cursor mode."""
        mode = self.var_loc_mode.get()
        if mode == "cursor":
            self.entry_x.config(state="disabled")
            self.entry_y.config(state="disabled")
            self.btn_pick.config(state="disabled")
            self.btn_capture.config(state="disabled")
        else:
            self.entry_x.config(state="normal")
            self.entry_y.config(state="normal")
            self.btn_pick.config(state="normal")
            self.btn_capture.config(state="normal")

    def _toggle_always_on_top(self):
        """Toggle keep window on top."""
        self.root.attributes("-topmost", self.var_always_on_top.get())

    def _start_pick_countdown(self):
        """Start a 3-second countdown to capture mouse coordinates."""
        if self.picking_countdown_active:
            return

        self.picking_countdown_active = True
        self.btn_pick.config(state="disabled", text="Move mouse...")

        def _countdown(remaining: int):
            if remaining > 0:
                cur_x, cur_y = pyautogui.position()
                self.lbl_coord_status.config(
                    text=f"⏳ Move cursor to target! Locking in {remaining}s... Current: ({cur_x}, {cur_y})",
                    fg=self.ACCENT_ORANGE,
                )
                self.root.after(1000, _countdown, remaining - 1)
            else:
                final_x, final_y = pyautogui.position()
                self._set_coordinates(final_x, final_y)
                self.lbl_coord_status.config(
                    text=f"✅ Locked target location: X={final_x}, Y={final_y}",
                    fg=self.ACCENT_GREEN,
                )
                self.btn_pick.config(state="normal", text="📍 Pick Location")
                self.picking_countdown_active = False

        _countdown(3)

    def _capture_current_cursor(self):
        """Immediately capture current mouse coordinate."""
        x, y = pyautogui.position()
        self._set_coordinates(x, y)
        self.lbl_coord_status.config(
            text=f"✅ Captured current position: X={x}, Y={y}",
            fg=self.ACCENT_GREEN,
        )

    def _set_coordinates(self, x: int, y: int):
        """Update coordinate entries."""
        self.entry_x.config(state="normal")
        self.entry_y.config(state="normal")
        self.entry_x.delete(0, tk.END)
        self.entry_x.insert(0, str(x))
        self.entry_y.delete(0, tk.END)
        self.entry_y.insert(0, str(y))
        if self.var_loc_mode.get() == "cursor":
            self.var_loc_mode.set("fixed")

    def _schedule_cursor_tracker(self):
        """Periodic background update for live cursor coordinate display."""
        try:
            cur_x, cur_y = pyautogui.position()
            if not self.picking_countdown_active:
                self.lbl_coord_status.config(
                    text=f"Live Cursor: ({cur_x}, {cur_y}) | Press [F7] anywhere to capture position",
                    fg=self.TEXT_MUTED,
                )
        except Exception:
            pass
        self.root.after(300, self._schedule_cursor_tracker)

    def _get_interval_seconds(self) -> float:
        """Parse interval inputs into seconds."""
        try:
            h = int(self.spin_hours.get() or 0)
            m = int(self.spin_mins.get() or 0)
            s = int(self.spin_secs.get() or 0)
            ms = int(self.spin_ms.get() or 0)
            total = (h * 3600) + (m * 60) + s + (ms / 1000.0)
            return max(0.005, total)  # Minimum 5ms safety limit
        except ValueError:
            return 1.0

    def _build_config_from_inputs(self) -> ClickConfig:
        """Assemble ClickConfig from UI controls."""
        try:
            x = int(self.entry_x.get())
            y = int(self.entry_y.get())
        except ValueError:
            x, y = self.screen_width // 2, self.screen_height // 2

        interval = self._get_interval_seconds()

        jitter_seconds = 0.0
        if self.var_jitter_enabled.get():
            try:
                jitter_seconds = max(0.0, float(self.spin_jitter_ms.get()) / 1000.0)
            except ValueError:
                jitter_seconds = 0.0

        repeat_count = 0
        if self.var_repeat_mode.get() == "count":
            try:
                repeat_count = max(1, int(self.spin_repeat_count.get()))
            except ValueError:
                repeat_count = 100

        return ClickConfig(
            mode=self.var_loc_mode.get(),
            x=x,
            y=y,
            interval_seconds=interval,
            jitter_seconds=jitter_seconds,
            button=self.var_button.get(),
            click_type=self.var_click_type.get(),
            repeat_count=repeat_count,
            restore_cursor=self.var_restore_cursor.get(),
        )

    def _toggle_clicker(self):
        """Start or stop clicking based on current engine state."""
        if self.engine.is_running:
            self._stop_clicker()
        else:
            config = self._build_config_from_inputs()
            self.engine.update_config(config)
            self.engine.start()

    def _stop_clicker(self):
        """Immediately stop clicking and release mouse."""
        if self.engine.is_running:
            self.engine.stop()

    def _safe_hotkey_toggle(self):
        """Thread-safe toggle called from global hotkey listener."""
        self.root.after(0, self._toggle_clicker)

    def _safe_hotkey_stop(self):
        """Immediate emergency stop called from global hotkey listener."""
        # Stop engine immediately in thread without waiting for event loop
        self.engine.stop()
        # Schedule visual UI update
        self.root.after(0, self._on_engine_stop, self.engine.clicks_done)

    def _safe_hotkey_capture(self):
        """Thread-safe coordinate capture called from global hotkey listener."""
        self.root.after(0, self._capture_current_cursor)

    def _on_engine_start(self):
        """GUI update when engine starts."""
        stop_key = self.var_stop_key.get()
        self.btn_toggle.config(
            text=f"⏹  STOP CLICKER  ({stop_key} or F6)",
            bg=self.ACCENT_RED,
            activebackground="#dc2626",
            fg="#ffffff",
        )
        self.lbl_status_badge.config(text="● RUNNING", fg=self.ACCENT_GREEN)
        self.lbl_clicks_count.config(text="Clicks: 0")

    def _on_engine_stop(self, total_clicks: int):
        """GUI update when engine stops."""
        self.btn_toggle.config(
            text="▶  START CLICKER  (F6)",
            bg=self.ACCENT_GREEN,
            activebackground="#10b981",
            fg="#0f172a",
        )
        self.lbl_status_badge.config(text="● STOPPED", fg=self.ACCENT_RED)
        self.lbl_clicks_count.config(text=f"Clicks: {total_clicks}")

    def _on_engine_click(self, current_count: int):
        """GUI update after each click."""
        self.lbl_clicks_count.config(text=f"Clicks: {current_count}")

    def _on_engine_error(self, error: Exception):
        """Handle engine error such as PyAutoGUI Fail-Safe trigger."""
        if isinstance(error, pyautogui.FailSafeException):
            msg = "Emergency Halt Triggered!\nThe mouse was moved to a screen corner, stopping the autoclicker immediately."
            messagebox.showwarning("Emergency Stop Triggered", msg)
        else:
            messagebox.showerror("AutoClicker Error", f"An error occurred: {str(error)}")

    def _on_closing(self):
        """Clean shutdown of background threads before exiting."""
        if self.engine.is_running:
            self.engine.stop()
        self.hotkeys.stop()
        self.root.destroy()
