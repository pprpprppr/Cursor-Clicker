#!/usr/bin/env bash
# AutoCursor Pro Launcher
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Launch application
python3 main.py "$@"
