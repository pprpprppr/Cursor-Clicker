"""Global Hotkey Manager.

Listens for global keypresses:
- ESC: Emergency Panic Stop (immediately halts clicking when active)
- F6: Start / Stop Toggle
- F7: Capture current mouse coordinates
- Configurable Stop Shortcut (ESC, F6, F8, F10, Pause)
"""

from typing import Callable, Optional
from pynput import keyboard


class HotkeyManager:
    """Manages global hotkeys using pynput keyboard listener."""

    KEY_OPTIONS = {
        "ESC": keyboard.Key.esc,
        "F6": keyboard.Key.f6,
        "F8": keyboard.Key.f8,
        "F10": keyboard.Key.f10,
        "PAUSE": keyboard.Key.pause,
    }

    def __init__(
        self,
        on_toggle: Optional[Callable[[], None]] = None,
        on_stop: Optional[Callable[[], None]] = None,
        on_capture_pos: Optional[Callable[[], None]] = None,
        is_active_check: Optional[Callable[[], bool]] = None,
        selected_stop_key: str = "ESC",
    ):
        self.on_toggle = on_toggle
        self.on_stop = on_stop
        self.on_capture_pos = on_capture_pos
        self.is_active_check = is_active_check
        self.selected_stop_key = selected_stop_key.upper()
        self._listener: Optional[keyboard.Listener] = None

    def set_stop_key(self, key_name: str) -> None:
        """Update the designated stop shortcut key name."""
        self.selected_stop_key = key_name.upper()

    def handle_press(self, key) -> None:
        """Handle key press event."""
        try:
            # 1. Panic Emergency Stop: Escape key or selected stop key
            # If clicking is active, ESC or selected stop key halts it instantly!
            target_stop_key = self.KEY_OPTIONS.get(self.selected_stop_key, keyboard.Key.esc)

            is_active = self.is_active_check() if self.is_active_check else True

            # If active and either ESC, F8, or the configured stop key is pressed -> STOP!
            if is_active and (key == keyboard.Key.esc or key == target_stop_key or key == keyboard.Key.f8):
                if self.on_stop:
                    self.on_stop()
                return

            # 2. Start / Stop Toggle (F6)
            if key == keyboard.Key.f6:
                if self.on_toggle:
                    self.on_toggle()
                return

            # 3. Capture Location (F7)
            if key == keyboard.Key.f7:
                if self.on_capture_pos:
                    self.on_capture_pos()
                return

        except Exception:
            pass

    def start(self) -> None:
        """Start listening for global key events."""
        if self._listener is not None:
            return

        self._listener = keyboard.Listener(on_press=self.handle_press)
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        """Stop listening for global key events."""
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
