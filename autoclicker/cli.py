"""Command Line Interface for Mouse Cursor Clicker.

Allows running the periodic clicker from terminal or shell scripts.
"""

import argparse
import sys
import time
import pyautogui

from autoclicker.engine import ClickerEngine, ClickConfig
from autoclicker.hotkeys import HotkeyManager


def run_cli(args_list=None):
    """Parse arguments and run clicker in terminal."""
    parser = argparse.ArgumentParser(
        description="AutoCursor Pro - Command Line Mouse Clicker",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--x", type=int, default=None, help="Target X coordinate")
    parser.add_argument("--y", type=int, default=None, help="Target Y coordinate")
    parser.add_argument("--pick", action="store_true", help="Interactive prompt to pick cursor location")
    parser.add_argument("--cursor", action="store_true", help="Click at current mouse cursor position dynamically")
    parser.add_argument("-i", "--interval", type=float, default=1.0, help="Interval between clicks in seconds")
    parser.add_argument("-j", "--jitter", type=float, default=0.0, help="Random interval jitter (+/- seconds)")
    parser.add_argument("-b", "--button", choices=["left", "right", "middle"], default="left", help="Mouse button")
    parser.add_argument("-t", "--type", choices=["single", "double", "triple"], default="single", help="Click type")
    parser.add_argument("-n", "--count", type=int, default=0, help="Total clicks to perform (0 = infinite)")
    parser.add_argument("--restore-cursor", action="store_true", help="Restore cursor to previous position after click")

    args = parser.parse_args(args_list)

    # Determine coordinates
    if args.cursor:
        mode = "cursor"
        target_x, target_y = 0, 0
        print("Mode: Dynamic cursor tracking")
    elif args.pick:
        print("\n[?] Move your mouse to the desired screen location and press ENTER...")
        try:
            input()
            target_x, target_y = pyautogui.position()
            mode = "fixed"
            print(f"[+] Captured location: X={target_x}, Y={target_y}")
        except KeyboardInterrupt:
            print("\nAborted.")
            sys.exit(0)
    elif args.x is not None and args.y is not None:
        mode = "fixed"
        target_x, target_y = args.x, args.y
        print(f"Mode: Fixed location (X={target_x}, Y={target_y})")
    else:
        # Default to current cursor position
        cur_x, cur_y = pyautogui.position()
        mode = "fixed"
        target_x, target_y = cur_x, cur_y
        print(f"Mode: Using initial cursor location (X={target_x}, Y={target_y})")

    config = ClickConfig(
        mode=mode,
        x=target_x,
        y=target_y,
        interval_seconds=max(0.005, args.interval),
        jitter_seconds=max(0.0, args.jitter),
        button=args.button,
        click_type=args.type,
        repeat_count=args.count,
        restore_cursor=args.restore_cursor,
    )

    engine = ClickerEngine(config)

    print("-" * 50)
    print("AutoCursor Pro CLI Running")
    print(f"Target:        {'Cursor' if mode == 'cursor' else f'({target_x}, {target_y})'}")
    print(f"Interval:      {config.interval_seconds:.3f}s (jitter: +/-{config.jitter_seconds:.3f}s)")
    print(f"Button:        {config.button} ({config.click_type})")
    print(f"Repeat:        {'Infinite (until stopped)' if config.repeat_count == 0 else f'{config.repeat_count} times'}")
    print("Hotkeys:       [ESC] or [F6] to STOP immediately, [Ctrl+C] to Exit")
    print("Safety:        Move mouse cursor to any corner of screen for emergency stop")
    print("-" * 50)

    # Hotkey support
    def stop():
        if engine.is_running:
            engine.stop()
            print("\n[STOPPED] Autoclicker stopped! Press F6 to resume, or Ctrl+C to exit.")

    def toggle():
        if engine.is_running:
            stop()
        else:
            engine.start()
            print("\n[RESUMED] Clicking active...")

    hotkeys = HotkeyManager(
        on_toggle=toggle,
        on_stop=stop,
        is_active_check=lambda: engine.is_running,
    )
    hotkeys.start()

    engine.on_click = lambda count: print(f"\r[+] Clicks performed: {count}", end="", flush=True)

    try:
        engine.start()
        while engine.is_running:
            time.sleep(0.1)
        print(f"\n[DONE] Finished {engine.clicks_done} clicks.")
    except KeyboardInterrupt:
        print("\n[STOPPING] Interrupted by user.")
    finally:
        engine.stop()
        hotkeys.stop()
        print("Exited cleanly.")
