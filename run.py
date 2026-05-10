"""
run.py — Unified entry point for all DedSeg bots.
Runs both the Main Bot and the GK Quiz Bot in parallel threads.
"""

import sys
import os
import threading

# Ensure DedSegBot/ is on the path
BOT_DIR = os.path.join(os.path.dirname(__file__), "DedSegBot")
if BOT_DIR not in sys.path:
    sys.path.insert(0, BOT_DIR)

from main import run_main_bot
from static_bot import run_static_bot


def main():
    print("=" * 50)
    print("  DedSeg Bot Ecosystem Starting")
    print("=" * 50)

    main_thread = threading.Thread(
        target=run_main_bot,
        name="MainBot",
        daemon=True,
    )
    gk_thread = threading.Thread(
        target=run_static_bot,
        name="GKBot",
        daemon=True,
    )

    main_thread.start()
    gk_thread.start()

    print("✅ Both bots launched. Press Ctrl+C to stop.")

    try:
        main_thread.join()
        gk_thread.join()
    except KeyboardInterrupt:
        print("\n⚠️ Shutdown signal received. Stopping bots...")
        sys.exit(0)


if __name__ == "__main__":
    main()
