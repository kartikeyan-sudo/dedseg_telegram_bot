"""
run.py — Unified entry point for all DedSeg bots.
Runs both the Main Bot and the GK Quiz Bot in parallel threads.
"""

import sys
import os
import threading

# Force UTF-8 output so emoji work on Windows terminals (CP1252 fix)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure DedSegBot/ is on the path
# Ensure DedSegBot/ is on the path
BOT_DIR = os.path.join(os.path.dirname(__file__), "DedSegBot")
if BOT_DIR not in sys.path:
    sys.path.insert(0, BOT_DIR)

import socket
import time

from DedSegBot.main import run_main_bot
from DedSegBot.static_bot import run_static_bot
from DedSegBot.config import BOT_TOKEN as MAIN_TOKEN
from DedSegBot.quiz_config import BOT_TOKEN as QUIZ_TOKEN

# ─── Single Instance Lock ─────────────────────────────────────────────────────

def check_already_running():
    """Check if another instance is holding the lock."""
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lock_socket.bind(("127.0.0.1", 47200))
        return lock_socket
    except socket.error:
        return None

def wait_for_lock(timeout=None):
    """Wait until the lock is available."""
    start_time = time.time()
    while True:
        lock = check_already_running()
        if lock:
            return lock
        if timeout and (time.time() - start_time) > timeout:
            return None
        time.sleep(5)

def start_bots():
    print("=" * 50)
    print("  DedSeg Bot Ecosystem Starting")
    print("=" * 50)

    # Check for identical tokens
    if MAIN_TOKEN == QUIZ_TOKEN:
        print("💡 [Info] Identical tokens detected. Running in Unified Mode.")
        # We'll still run the scheduler from the static_bot logic but skip its polling
        from DedSegBot.scheduler import start_scheduler
        start_scheduler()
        
        main_thread = threading.Thread(target=run_main_bot, name="MainBot", daemon=True)
        main_thread.start()
        return [main_thread]

    main_thread = threading.Thread(target=run_main_bot, name="MainBot", daemon=True)
    gk_thread = threading.Thread(target=run_static_bot, name="GKBot", daemon=True)

    main_thread.start()
    gk_thread.start()

    print("✅ Bots launched. Monitoring threads...")
    return [main_thread, gk_thread]


def main():
    print("⏳ Waiting for bot lock...")
    lock = wait_for_lock(timeout=60) # Wait up to 60s for old instance to die
    if not lock:
        print("⚠️ [Error] Could not acquire lock. Another instance might be stuck.")
        sys.exit(1)

    threads = start_bots()

    try:
        for t in threads:
            while t.is_alive():
                t.join(1)
    except KeyboardInterrupt:
        print("\n⚠️ Shutdown signal received. Stopping bots...")
        sys.exit(0)


if __name__ == "__main__":
    main()
