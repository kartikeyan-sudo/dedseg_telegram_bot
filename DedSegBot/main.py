import json
import time
import requests
from broadcast import broadcast_message
from config import BOT_TOKEN, ADMIN_ID, GROUPS

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
OFFSET_FILE = "DedSegBot/update_offset.txt"

GROUP_MAP = {str(group["id"]): group["name"] for group in GROUPS}

MENU_INLINE = {
    "inline_keyboard": [
        [{"text": "Test Bot", "callback_data": "test"}],
        [{"text": "Broadcast All", "callback_data": "broadcast_all"}],
        [{"text": "Broadcast Group", "callback_data": "broadcast_group"}],
        [{"text": "Message User", "callback_data": "message_user"}],
        [{"text": "Cancel", "callback_data": "cancel"}]
    ]
}

CANCEL_INLINE = {
    "inline_keyboard": [
        [{"text": "Cancel", "callback_data": "cancel"}]
    ]
}


def set_my_commands():
    commands = [
        {"command": "start", "description": "Open the DedSeg menu"},
        {"command": "menu", "description": "Show bot commands"},
        {"command": "test", "description": "Ping the bot"},
        {"command": "broadcast", "description": "Send a broadcast message"},
        {"command": "help", "description": "Show help text"},
        {"command": "cancel", "description": "Cancel the current action"}
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


pending_actions = {}


def set_pending_action(user_id, action):
    pending_actions[user_id] = action


def get_pending_action(user_id):
    return pending_actions.get(user_id)


def clear_pending_action(user_id):
    pending_actions.pop(user_id, None)


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
    group_lines = "\n".join([f"{idx + 1}. {group['name']}" for idx, group in enumerate(GROUPS)])
    return (
        "📌 DedSeg Main Bot Menu:\n"
        "Use the buttons below to control the bot.\n"
        "\nButtons:\n"
        "• Test Bot\n"
        "• Broadcast All\n"
        "• Broadcast Group\n"
        "• Message User\n"
        "• Cancel\n"
        "\nCommands work too: /help, /cancel, /debug\n"
        "\nGroups:\n"
        f"{group_lines}\n"
        "When you select Broadcast Group, the bot will remain in that group until you press Cancel."
    )


def handle_update(update):
    if update.get("callback_query"):
        callback = update["callback_query"]
        callback_data = callback.get("data", "")
        chat_id = callback["message"]["chat"]["id"]
        user_id = callback["from"]["id"]
        callback_id = callback["id"]

        if user_id != ADMIN_ID:
            answer_callback_query(callback_id, "❌ Only the admin can use this bot.")
            return

        if callback_data == "test":
            send_message(chat_id, "✅ DedSeg Main Bot is online and ready.")
            answer_callback_query(callback_id, "Test completed.")
            return

        if callback_data == "menu":
            send_message(chat_id, build_menu_text(), reply_markup=MENU_INLINE)
            answer_callback_query(callback_id)
            return

        if callback_data == "broadcast_all":
            if user_id != ADMIN_ID:
                send_message(chat_id, "❌ Only the admin can send broadcasts.")
                answer_callback_query(callback_id)
                return
            send_message(chat_id, "✉️ Broadcast All mode enabled. Send messages now. Use /cancel to stop.", reply_markup=MENU_INLINE)
            set_pending_action(user_id, {"action": "broadcast_all"})
            answer_callback_query(callback_id, "Broadcast All mode enabled.")
            return

        if callback_data == "broadcast_group":
            if user_id != ADMIN_ID:
                send_message(chat_id, "❌ Only the admin can send broadcasts.")
                answer_callback_query(callback_id)
                return
            buttons = [[{"text": group["name"], "callback_data": f"select_group|{group['id']}"}] for group in GROUPS]
            keyboard = {"inline_keyboard": buttons}
            send_message(chat_id, "📌 Select a group to send messages to. This will stay active until you press Cancel.", reply_markup=keyboard)
            answer_callback_query(callback_id)
            return

        if callback_data == "message_user":
            if user_id != ADMIN_ID:
                send_message(chat_id, "❌ Only the admin can message users.")
                answer_callback_query(callback_id)
                return
            send_message(chat_id, "👤 Send the target user ID now. Example: 123456789", reply_markup=MENU_INLINE)
            set_pending_action(user_id, {"action": "message_user_id"})
            answer_callback_query(callback_id, "Send the target user ID.")
            return

        if callback_data == "cancel":
            clear_pending_action(user_id)
            send_message(chat_id, "✅ Action cancelled. Back to main menu.", reply_markup=MENU_INLINE)
            answer_callback_query(callback_id)
            return

        if callback_data.startswith("select_group|"):
            if user_id != ADMIN_ID:
                answer_callback_query(callback_id, "Only admins can send broadcasts.")
                return
            group_id = callback_data.split("|", 1)[1]
            group_name = GROUP_MAP.get(group_id, group_id)
            send_message(chat_id, f"✉️ Broadcast Group mode enabled for <b>{group_name}</b>. Send messages now. Use /cancel to stop.", reply_markup=MENU_INLINE)
            set_pending_action(user_id, {"action": "broadcast_group", "group_id": group_id})
            answer_callback_query(callback_id, f"Selected {group_name}.")
            return

        answer_callback_query(callback_id, "Unknown action.")
        return

    message = update.get("message")
    if not message:
        return

    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()
    user_id = message["from"]["id"]
    chat_type = message["chat"].get("type")

    if chat_type == "private" and user_id != ADMIN_ID:
        user_name = message["from"].get("username") or message["from"].get("first_name", "Unknown")
        forwarded_text = f"📩 Message from {user_name} (ID: {user_id}):\n{text}"
        send_message(ADMIN_ID, forwarded_text)

    pending = get_pending_action(user_id)
    if pending:
        if text.startswith("/cancel"):
            clear_pending_action(user_id)
            send_message(chat_id, "✅ Action cancelled. Back to main menu.", reply_markup=MENU_INLINE)
            return

        if pending["action"] == "broadcast_all":
            broadcast_message(text)
            send_message(chat_id, "✅ Message broadcast to all groups. Continue sending or use /cancel to exit.")
            return

        if pending["action"] == "broadcast_group":
            target_id = pending.get("group_id")
            group_name = GROUP_MAP.get(target_id, target_id)
            broadcast_message(text, target_id=target_id)
            send_message(chat_id, f"✅ Message sent to <b>{group_name}</b>. Continue sending or use /cancel to exit.")
            return

        if pending["action"] == "message_user_id":
            if not text.isdigit() and not text.startswith("@"):
                send_message(chat_id, "❌ Invalid user identifier. Send a numeric user ID or @username, or use /cancel.")
                return
            target_id = text
            send_message(chat_id, f"👤 User target set to <b>{target_id}</b>. Now send the message. Use /cancel to stop.", reply_markup=MENU_INLINE)
            set_pending_action(user_id, {"action": "message_user", "user_id": target_id})
            return

        if pending["action"] == "message_user":
            target_id = pending.get("user_id")
            send_message(target_id, f"📩 Message from DedSeg Admin:\n{text}")
            send_message(chat_id, f"✅ Message sent to <b>{target_id}</b>. Continue sending or use /cancel to exit.")
            return

    if text.startswith("/start"):
        if user_id != ADMIN_ID:
            send_message(chat_id, "❌ This bot is restricted to the admin only.")
            return
        send_message(chat_id, "👋 Welcome to DedSeg Main Bot!", reply_markup=MENU_INLINE)
        send_message(chat_id, build_menu_text(), reply_markup=MENU_INLINE)
        return

    if text.startswith("/menu"):
        if user_id != ADMIN_ID:
            send_message(chat_id, "❌ Only the admin can use this bot.")
            return
        send_message(chat_id, build_menu_text(), reply_markup=MENU_INLINE)
        return

    if text.startswith("/test"):
        if user_id != ADMIN_ID:
            send_message(chat_id, "❌ Only the admin can use this bot.")
            return
        send_message(chat_id, "✅ DedSeg Main Bot is online and ready.")
        return

    if text.startswith("/help"):
        if user_id != ADMIN_ID:
            send_message(chat_id, "❌ Only the admin can use this bot.")
            return
        send_message(chat_id, build_menu_text(), reply_markup=MENU_INLINE)
        return

    if text.startswith("/debug"):
        if user_id != ADMIN_ID:
            send_message(chat_id, "❌ Only the admin can use this bot.")
            return
        send_message(chat_id, f"Your user id: {user_id}\nAdmin id: {ADMIN_ID}")
        return

    if text.startswith("/broadcast"):
        if user_id != ADMIN_ID:
            send_message(chat_id, "❌ Only the admin can send broadcasts.")
            return
        parts = text.split(" ", 1)
        if len(parts) < 2 or not parts[1].strip():
            send_message(chat_id, "Usage: /broadcast Your message here")
            return
        broadcast_message(parts[1].strip())
        send_message(chat_id, "✅ Broadcast sent to all configured groups.")
        return

    if text.startswith("/cancel"):
        if user_id != ADMIN_ID:
            send_message(chat_id, "❌ Only the admin can use this bot.")
            return
        clear_pending_action(user_id)
        send_message(chat_id, "✅ Action cancelled. Back to main menu.", reply_markup=MENU_INLINE)
        return

    if user_id != ADMIN_ID:
        return

    send_message(chat_id, "⚠️ Unknown command. Use /menu to see available commands.", reply_markup=MENU_INLINE)


def run_main_bot():
    print("DedSeg Main Bot is running with command support.")
    set_my_commands()
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
    run_main_bot()
