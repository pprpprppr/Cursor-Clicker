"""Clicker Engine for mouse automation.

Handles high-precision periodic mouse clicks in a dedicated background thread
with configurable target locations, interval, jitter, and safety limits.
"""

from dataclasses import dataclass
import random
import threading
import time
from typing import Callable, Optional
import pyautogui

# Set PyAutoGUI settings
pyautogui.PAUSE = 0.01  # Minimal default pause
pyautogui.FAILSAFE = True  # Move mouse to any corner to abort


@dataclass
class ClickConfig:
    """Configuration for click automation."""
    mode: str = "fixed"  # "fixed" or "cursor"
    x: int = 0
    y: int = 0
    interval_seconds: float = 1.0  # seconds between clicks
    jitter_seconds: float = 0.0   # random variation (+/- jitter)
    button: str = "left"          # "left", "right", "middle"
    click_type: str = "single"    # "single", "double", "triple"
    repeat_count: int = 0         # 0 means infinite / until stopped
    restore_cursor: bool = False  # return cursor to origin after click


class ClickerEngine:
    """Threaded mouse clicker engine."""

    def __init__(self, config: Optional[ClickConfig] = None):
        self.config = config or ClickConfig()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
        self._clicks_done = 0

        # Event callbacks
        self.on_start: Optional[Callable[[], None]] = None
        self.on_stop: Optional[Callable[[int], None]] = None
        self.on_click: Optional[Callable[[int], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None

    @property
    def is_running(self) -> bool:
        """Return True if clicker is currently running."""
        return self._running

    @property
    def clicks_done(self) -> int:
        """Return total clicks executed in current session."""
        return self._clicks_done

    def update_config(self, config: ClickConfig) -> None:
        """Update click configuration."""
        self.config = config

    def start(self) -> bool:
        """Start clicking loop in background thread."""
        if self._running:
            return False

        self._stop_event.clear()
        self._running = True
        self._clicks_done = 0

        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="ClickerEngineThread")
        self._thread.start()

        if self.on_start:
            try:
                self.on_start()
            except Exception:
                pass

        return True

    def stop(self) -> bool:
        """Stop clicking loop."""
        if not self._running:
            return False

        self._stop_event.set()
        self._running = False

        if self._thread and self._thread.is_alive():
            if threading.current_thread() != self._thread:
                self._thread.join(timeout=0.2)

        if self.on_stop:
            try:
                self.on_stop(self._clicks_done)
            except Exception:
                pass

        return True

    def toggle(self) -> bool:
        """Toggle between running and stopped state."""
        if self._running:
            self.stop()
            return False
        else:
            self.start()
            return True

    def _execute_click(self) -> None:
        """Perform a single click operation based on config."""
        clicks_map = {
            "single": 1,
            "double": 2,
            "triple": 3,
        }
        click_count = clicks_map.get(self.config.click_type, 1)
        btn = self.config.button if self.config.button in ("left", "right", "middle") else "left"

        if self.config.mode == "fixed":
            target_x = int(self.config.x)
            target_y = int(self.config.y)

            if self.config.restore_cursor:
                orig_x, orig_y = pyautogui.position()
                pyautogui.click(x=target_x, y=target_y, clicks=click_count, button=btn)
                pyautogui.moveTo(orig_x, orig_y)
            else:
                pyautogui.click(x=target_x, y=target_y, clicks=click_count, button=btn)
        else:
            # Click at current mouse cursor position
            pyautogui.click(clicks=click_count, button=btn)

    def _run_loop(self) -> None:
        """Main execution loop for background thread."""
        try:
            while not self._stop_event.is_set():
                # Perform click
                self._execute_click()
                self._clicks_done += 1

                if self.on_click:
                    try:
                        self.on_click(self._clicks_done)
                    except Exception:
                        pass

                # Check if repeat count reached
                if self.config.repeat_count > 0 and self._clicks_done >= self.config.repeat_count:
                    break

                # Calculate delay with optional jitter
                delay = self.config.interval_seconds
                if self.config.jitter_seconds > 0:
                    delta = random.uniform(-self.config.jitter_seconds, self.config.jitter_seconds)
                    delay = max(0.005, delay + delta)

                # Wait using event with timeout (allows immediate interruption)
                if self._stop_event.wait(timeout=delay):
                    break

        except pyautogui.FailSafeException as ex:
            # PyAutoGUI fail-safe triggered (user moved mouse to screen corner)
            if self.on_error:
                try:
                    self.on_error(ex)
                except Exception:
                    pass
        except Exception as ex:
            if self.on_error:
                try:
                    self.on_error(ex)
                except Exception:
                    pass
        finally:
            self._running = False
            if self.on_stop:
                try:
                    self.on_stop(self._clicks_done)
                except Exception:
                    pass
