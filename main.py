#!/usr/bin/env python3
"""Main entrypoint for Mouse Cursor Clicker application.

Launches the Tkinter GUI by default, or the CLI mode if flags are provided.
"""

import sys
import tkinter as tk
from autoclicker.cli import run_cli
from autoclicker.ui import ModernAutoClickerUI


def main():
    # If command line arguments are provided (other than just script name), run CLI mode
    cli_flags = {"--cli", "--x", "--y", "--pick", "--cursor", "-i", "--interval", "-n", "--count", "-b", "--button", "-h", "--help"}
    has_cli_args = any(arg in cli_flags for arg in sys.argv[1:])

    if has_cli_args:
        # Strip --cli if present
        filtered_args = [arg for arg in sys.argv[1:] if arg != "--cli"]
        run_cli(filtered_args)
    else:
        root = tk.Tk()
        app = ModernAutoClickerUI(root)
        root.mainloop()


if __name__ == "__main__":
    main()
