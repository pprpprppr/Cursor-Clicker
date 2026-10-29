"""Test suite for AutoCursor Pro."""

import unittest
import time
import tkinter as tk
from unittest.mock import patch, MagicMock
from pynput import keyboard

from autoclicker.engine import ClickerEngine, ClickConfig
from autoclicker.hotkeys import HotkeyManager
from autoclicker.ui import ModernAutoClickerUI


class TestClickerEngine(unittest.TestCase):
    """Test ClickerEngine core functionality."""

    def test_config_initialization(self):
        config = ClickConfig(x=100, y=200, interval_seconds=0.5, button="left", repeat_count=5)
        self.assertEqual(config.x, 100)
        self.assertEqual(config.y, 200)
        self.assertEqual(config.interval_seconds, 0.5)
        self.assertEqual(config.repeat_count, 5)

    @patch("pyautogui.click")
    def test_engine_fixed_count_execution(self, mock_click):
        """Verify engine executes exact number of clicks and stops automatically."""
        config = ClickConfig(
            mode="fixed",
            x=500,
            y=400,
            interval_seconds=0.02,
            repeat_count=3,
        )
        engine = ClickerEngine(config)

        click_counts = []
        engine.on_click = lambda c: click_counts.append(c)

        stopped_called = []
        engine.on_stop = lambda total: stopped_called.append(total)

        engine.start()
        # Wait for thread to finish 3 clicks
        time.sleep(0.2)

        self.assertFalse(engine.is_running)
        self.assertEqual(engine.clicks_done, 3)
        self.assertEqual(click_counts, [1, 2, 3])
        self.assertEqual(stopped_called, [3])
        self.assertEqual(mock_click.call_count, 3)

    @patch("pyautogui.click")
    def test_engine_manual_stop(self, mock_click):
        """Verify engine can be stopped mid-execution."""
        config = ClickConfig(
            mode="cursor",
            interval_seconds=0.05,
            repeat_count=100,
        )
        engine = ClickerEngine(config)
        engine.start()
        self.assertTrue(engine.is_running)

        time.sleep(0.12)
        engine.stop()

        self.assertFalse(engine.is_running)
        self.assertGreater(engine.clicks_done, 0)
        self.assertLess(engine.clicks_done, 10)


class TestHotkeyManager(unittest.TestCase):
    """Test HotkeyManager."""

    def test_hotkey_lifecycle(self):
        toggle_mock = MagicMock()
        stop_mock = MagicMock()
        capture_mock = MagicMock()
        hm = HotkeyManager(on_toggle=toggle_mock, on_stop=stop_mock, on_capture_pos=capture_mock)
        hm.start()
        self.assertIsNotNone(hm._listener)
        hm.stop()
        self.assertIsNone(hm._listener)

    def test_esc_stop_trigger(self):
        """Verify ESC key triggers on_stop when active."""
        stop_mock = MagicMock()
        hm = HotkeyManager(on_stop=stop_mock, is_active_check=lambda: True)
        hm.handle_press(keyboard.Key.esc)
        stop_mock.assert_called_once()

    def test_esc_ignored_when_inactive(self):
        """Verify ESC key does nothing when clicker is not active."""
        stop_mock = MagicMock()
        hm = HotkeyManager(on_stop=stop_mock, is_active_check=lambda: False)
        hm.handle_press(keyboard.Key.esc)
        stop_mock.assert_not_called()


class TestUIInstantiation(unittest.TestCase):
    """Test that UI initializes and cleans up without errors."""

    def test_ui_build_and_destroy(self):
        root = tk.Tk()
        root.withdraw()
        app = ModernAutoClickerUI(root)

        # Check default coordinate inputs and stop buttons exist
        self.assertTrue(hasattr(app, "entry_x"))
        self.assertTrue(hasattr(app, "entry_y"))
        self.assertTrue(hasattr(app, "btn_toggle"))
        self.assertTrue(hasattr(app, "btn_emergency_stop"))
        self.assertEqual(app.var_stop_key.get(), "ESC")

        # Verify interval calculation
        app.spin_hours.delete(0, tk.END)
        app.spin_hours.insert(0, "0")
        app.spin_mins.delete(0, tk.END)
        app.spin_mins.insert(0, "1")
        app.spin_secs.delete(0, tk.END)
        app.spin_secs.insert(0, "30")
        app.spin_ms.delete(0, tk.END)
        app.spin_ms.insert(0, "500")

        self.assertAlmostEqual(app._get_interval_seconds(), 90.5)

        # Verify clean closing
        app._on_closing()


if __name__ == "__main__":
    unittest.main()
