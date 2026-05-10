import json
import time
import requests
from quiz import send_daily_quiz
from quiz_config import BOT_TOKEN
from scheduler import start_scheduler

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
OFFSET_FILE = "DedSegBot/quiz_update_offset.txt"

MENU_KEYBOARD = {
    "keyboard": [
        ["/quiz", "/menu"],
        ["/help"]
    ],
    "resize_keyboard": True,
    "one_time_keyboard": False
}

MENU_INLINE = {
    "inline_keyboard": [
        [{"text": "Start Quiz Now", "callback_data": "run_quiz"}],
        [{"text": "Show Menu", "callback_data": "menu"}]
    ]
}


def set_my_commands():
    commands = [
        {"command": "start", "description": "Show bot menu"},
        {"command": "menu", "description": "Show available commands"},
        {"command": "quiz", "description": "Run the quiz now"},
        {"command": "help", "description": "Show help text"}
    ]
    response = requests.post(
        f"{BASE_URL}/setMyCommands",
        json={"commands": commands}
    )
    return response.json()


def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup is not None:
        payload["reply_markup"] = json.dumps(reply_markup)
    response = requests.post(f"{BASE_URL}/sendMessage", data=payload)
    return response.json()


def answer_callback_query(callback_query_id, text=None, show_alert=False):
    payload = {
        "callback_query_id": callback_query_id,
        "show_alert": show_alert
    }
    if text is not None:
        payload["text"] = text
    requests.post(f"{BASE_URL}/answerCallbackQuery", data=payload)


def get_updates(offset=None, timeout=20):
    params = {"timeout": timeout}
    if offset:
        params["offset"] = offset
    response = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=timeout + 10)
    return response.json()


def save_offset(offset):
    with open(OFFSET_FILE, "w", encoding="utf-8") as f:
        f.write(str(offset))


def load_offset():
    try:
        with open(OFFSET_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except Exception:
        return None


def build_menu_text():
    return (
        "📌 Daily Static GK Bot Commands:\n"
        "/start - Show the menu\n"
        "/menu - Show this menu again\n"
        "/quiz - Run the quiz immediately\n"
        "/help - Show help text\n"
        "\nScheduled quizzes still run at 8 AM, 1 PM, and 9 PM."
    )


def handle_update(update):
    if update.get("callback_query"):
        callback = update["callback_query"]
        data = callback.get("data", "")
        chat_id = callback["message"]["chat"]["id"]
        callback_id = callback["id"]

        if data == "run_quiz":
            send_message(chat_id, "⏳ Starting the quiz now...", reply_markup=MENU_INLINE)
            send_daily_quiz()
            answer_callback_query(callback_id, "Quiz started successfully.")
            return

        if data == "menu":
            send_message(chat_id, build_menu_text(), reply_markup=MENU_INLINE)
            answer_callback_query(callback_id)
            return

        answer_callback_query(callback_id, "Unknown action.")
        return

    message = update.get("message")
    if not message:
        return

    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip().lower()

    if text.startswith("/start"):
        send_message(chat_id, "👋 Welcome to Daily Static GK Bot!", reply_markup=MENU_INLINE)
        send_message(chat_id, build_menu_text(), reply_markup=MENU_KEYBOARD)
        return

    if text.startswith("/menu") or text.startswith("/help"):
        send_message(chat_id, build_menu_text(), reply_markup=MENU_INLINE)
        return

    if text.startswith("/quiz"):
        send_message(chat_id, "⏳ Starting the quiz now...", reply_markup=MENU_INLINE)
        send_daily_quiz()
        return

    send_message(chat_id, "⚠️ Unknown command. Use /menu to see available commands.", reply_markup=MENU_KEYBOARD)


def run_static_bot():
    print("Daily Static GK Bot is running with scheduled quiz, fact, and motivation tasks.")
    set_my_commands()
    start_scheduler()

    offset = load_offset()
    while True:
        try:
            updates = get_updates(offset=offset, timeout=30)
            if not updates.get("ok"):
                time.sleep(5)
                continue

            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                print("Received update:", update)
                handle_update(update)
                save_offset(offset)

        except requests.exceptions.RequestException as exc:
            print("Network error:", exc)
            time.sleep(5)
        except Exception as exc:
            print("Bot error:", exc)
            time.sleep(5)


if __name__ == "__main__":
    run_static_bot()
