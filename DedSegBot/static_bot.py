import json
import os
import time
import requests
from DedSegBot.quiz import send_daily_quiz
from DedSegBot.quiz_config import BOT_TOKEN, QUIZ_CHAT_ID, ADMIN_ID
from DedSegBot.scheduler import start_scheduler

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
OFFSET_FILE = os.path.join(os.path.dirname(__file__), "quiz_update_offset.txt")

ADMIN_MENU_INLINE = {
    "inline_keyboard": [
        [{"text": "📚 Run Quiz Now", "callback_data": "run_quiz"}],
        [{"text": "📋 Menu", "callback_data": "menu"}],
    ]
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup is not None:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        r = requests.post(f"{BASE_URL}/sendMessage", data=payload, timeout=15)
        return r.json()
    except Exception as e:
        print(f"[gk_bot send_message] error: {e}")
        return {}


def answer_callback_query(cb_id, text=None, show_alert=False):
    payload = {"callback_query_id": cb_id, "show_alert": show_alert}
    if text:
        payload["text"] = text
    try:
        requests.post(f"{BASE_URL}/answerCallbackQuery", data=payload, timeout=10)
    except Exception as e:
        print(f"[gk_bot answer_callback] error: {e}")


def get_updates(offset=None, timeout=30):
    params = {"timeout": timeout}
    if offset:
        params["offset"] = offset
    try:
        r = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=timeout + 10)
        return r.json()
    except Exception as e:
        print(f"[gk_bot get_updates] error: {e}")
        return {"ok": False}


def save_offset(offset):
    try:
        with open(OFFSET_FILE, "w", encoding="utf-8") as f:
            f.write(str(offset))
    except Exception as e:
        print(f"[gk_bot save_offset] error: {e}")


def load_offset():
    try:
        with open(OFFSET_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except Exception:
        return None


def set_my_commands():
    """Admin sees quiz commands; all other users see no commands."""
    admin_cmds = [
        {"command": "start", "description": "Show menu"},
        {"command": "quiz",  "description": "Run quiz now"},
        {"command": "menu",  "description": "Show menu"},
        {"command": "help",  "description": "Help"},
    ]
    try:
        requests.post(f"{BASE_URL}/setMyCommands", json={
            "commands": admin_cmds,
            "scope": {"type": "chat", "chat_id": ADMIN_ID},
        }, timeout=10)
        requests.post(f"{BASE_URL}/setMyCommands", json={
            "commands": [],
            "scope": {"type": "all_private_chats"},
        }, timeout=10)
        print("✅ GK Bot commands scoped to admin only.")
    except Exception as e:
        print(f"[set_my_commands] error: {e}")


def build_menu_text():
    return (
        "📌 <b>Daily Static GK Bot</b>\n\n"
        "🎯 Scheduled content runs at:\n"
        "  • 8:00 AM — Daily Quiz\n"
        "  • 1:00 PM — GK Fact\n"
        "  • 9:00 PM — Motivation\n\n"
        "Stay sharp and keep learning! 🚀"
    )


# ─── Update handler ───────────────────────────────────────────────────────────

def handle_update(update):
    # ── Callbacks ────────────────────────────────────────────────────────────
    if update.get("callback_query"):
        cb = update["callback_query"]
        data = cb.get("data", "")
        chat_id = cb["message"]["chat"]["id"]
        user_id = cb["from"]["id"]
        cb_id = cb["id"]

        if data == "run_quiz":
            # Only admin can trigger quiz manually
            if user_id != ADMIN_ID:
                answer_callback_query(cb_id)
                return
            send_message(chat_id, "⏳ Starting quiz now...")
            try:
                send_daily_quiz()
                send_message(chat_id, "✅ Quiz sent successfully!", reply_markup=ADMIN_MENU_INLINE)
                answer_callback_query(cb_id, "✅ Quiz started!")
            except Exception as e:
                print(f"[run_quiz] error: {e}")
                send_message(chat_id, "❌ Quiz failed to run. Check server logs.")
                answer_callback_query(cb_id, "❌ Error")
            return

        if data == "menu":
            send_message(chat_id, build_menu_text(), reply_markup=ADMIN_MENU_INLINE if user_id == ADMIN_ID else None)
            answer_callback_query(cb_id)
            return

        answer_callback_query(cb_id)
        return

    # ── Messages ─────────────────────────────────────────────────────────────
    message = update.get("message")
    if not message:
        return

    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()
    user_id = message["from"]["id"]
    chat_type = message["chat"].get("type", "private")
    first_name = message["from"].get("first_name", "there")
    username = message["from"].get("username", "")
    message_id = message["message_id"]

    # ── Non-admin private chat: Livegram welcome + message forwarding ─────────
    if chat_type == "private" and user_id != ADMIN_ID:
        if text.startswith("/start"):
            send_message(
                chat_id,
                f"👋 Hi <b>{first_name}</b>! Welcome to <b>Daily Static GK</b>.\n\n"
                "📚 We deliver daily quizzes, GK facts, and motivation to our channels.\n"
                "🎯 Join our community to stay sharp every day!\n\n"
                "📩 Send us a message anytime and our team will respond.",
            )
            return
        # Forwarding disabled in GK Bot to avoid duplicate notifications.
        # Use the Main Bot for contacting the team.
        return

    # ── Non-admin non-private: ignore ────────────────────────────────────────
    if user_id != ADMIN_ID:
        return

    # ── Admin commands ────────────────────────────────────────────────────────
    cmd = text.split()[0].lower() if text else ""

    if cmd in ("/start", "/menu", "/help"):
        send_message(chat_id, build_menu_text(), reply_markup=ADMIN_MENU_INLINE)
        return

    if cmd == "/quiz":
        send_message(chat_id, "⏳ Starting quiz now...")
        try:
            send_daily_quiz()
            send_message(chat_id, "✅ Quiz sent successfully!", reply_markup=ADMIN_MENU_INLINE)
        except Exception as e:
            print(f"[/quiz command] error: {e}")
            send_message(chat_id, "❌ Quiz failed. Check server logs.")
        return


# ─── Entry point ──────────────────────────────────────────────────────────────

def run_static_bot():
    print("🚀 Daily Static GK Bot starting...")
    set_my_commands()
    start_scheduler()
    offset = load_offset()
    print("✅ Daily Static GK Bot is running.")

    while True:
        try:
            updates = get_updates(offset=offset, timeout=30)
            if not updates.get("ok"):
                time.sleep(5)
                continue
            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                handle_update(update)
                save_offset(offset)
        except requests.exceptions.RequestException as exc:
            print(f"[gk_bot] Network error: {exc}")
            time.sleep(5)
        except Exception as exc:
            print(f"[gk_bot] Error: {exc}")
            time.sleep(5)


if __name__ == "__main__":
    run_static_bot()
