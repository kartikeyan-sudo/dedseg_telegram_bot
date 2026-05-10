import json
import os
import time
import requests
from datetime import datetime
from broadcast import broadcast_message
from config import BOT_TOKEN, ADMIN_ID, GROUPS

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
OFFSET_FILE = os.path.join(os.path.dirname(__file__), "update_offset.txt")
GROUP_MAP = {str(group["id"]): group["name"] for group in GROUPS}

BOT_START_TIME = datetime.now()
last_broadcast_time = None
pending_actions = {}

# ─── Keyboards ────────────────────────────────────────────────────────────────

ADMIN_MENU_INLINE = {
    "inline_keyboard": [
        [
            {"text": "🔔 Broadcast All", "callback_data": "broadcast_all"},
            {"text": "📌 Broadcast Group", "callback_data": "broadcast_group"},
        ],
        [
            {"text": "👤 Message User", "callback_data": "message_user"},
            {"text": "📊 Stats", "callback_data": "stats"},
        ],
        [
            {"text": "📋 List Groups", "callback_data": "list_groups"},
            {"text": "🧪 Test Bot", "callback_data": "test"},
        ],
        [{"text": "❌ Cancel Action", "callback_data": "cancel"}],
    ]
}

CANCEL_INLINE = {
    "inline_keyboard": [
        [{"text": "❌ Cancel", "callback_data": "cancel"}]
    ]
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup is not None:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        r = requests.post(f"{BASE_URL}/sendMessage", data=payload, timeout=15)
        return r.json()
    except Exception as e:
        print(f"[send_message] error: {e}")
        return {}


def answer_callback_query(callback_query_id, text=None, show_alert=False):
    payload = {"callback_query_id": callback_query_id, "show_alert": show_alert}
    if text:
        payload["text"] = text
    try:
        requests.post(f"{BASE_URL}/answerCallbackQuery", data=payload, timeout=10)
    except Exception as e:
        print(f"[answer_callback] error: {e}")


def get_updates(offset=None, timeout=30):
    params = {"timeout": timeout}
    if offset:
        params["offset"] = offset
    try:
        r = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=timeout + 10)
        return r.json()
    except Exception as e:
        print(f"[get_updates] error: {e}")
        return {"ok": False}


def save_offset(offset):
    try:
        with open(OFFSET_FILE, "w", encoding="utf-8") as f:
            f.write(str(offset))
    except Exception as e:
        print(f"[save_offset] error: {e}")


def load_offset():
    try:
        with open(OFFSET_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except Exception:
        return None


def set_pending_action(user_id, action):
    pending_actions[user_id] = action


def get_pending_action(user_id):
    return pending_actions.get(user_id)


def clear_pending_action(user_id):
    pending_actions.pop(user_id, None)


# ─── Scoped commands (admin only) ─────────────────────────────────────────────

def set_my_commands():
    """Register admin commands only for admin's chat; everyone else sees nothing."""
    admin_cmds = [
        {"command": "start",     "description": "Open admin panel"},
        {"command": "menu",      "description": "Show admin menu"},
        {"command": "broadcast", "description": "Quick broadcast to all groups"},
        {"command": "reply",     "description": "Reply to a user: /reply <id> <msg>"},
        {"command": "stats",     "description": "Show bot statistics"},
        {"command": "test",      "description": "Ping the bot"},
        {"command": "cancel",    "description": "Cancel current action"},
        {"command": "help",      "description": "Show help"},
    ]
    try:
        # Set commands for admin's private chat
        requests.post(f"{BASE_URL}/setMyCommands", json={
            "commands": admin_cmds,
            "scope": {"type": "chat", "chat_id": ADMIN_ID},
        }, timeout=10)
        # Clear commands for all other private chats (users see NO commands)
        requests.post(f"{BASE_URL}/setMyCommands", json={
            "commands": [],
            "scope": {"type": "all_private_chats"},
        }, timeout=10)
        print("✅ Commands scoped to admin only.")
    except Exception as e:
        print(f"[set_my_commands] error: {e}")


# ─── Text builders ─────────────────────────────────────────────────────────────

def build_admin_menu_text():
    uptime = datetime.now() - BOT_START_TIME
    h, rem = divmod(int(uptime.total_seconds()), 3600)
    m, _ = divmod(rem, 60)
    return (
        "🎛 <b>DedSeg Admin Panel</b>\n"
        f"⏱ Uptime: {h}h {m}m  |  👥 Groups: {len(GROUPS)}\n\n"
        "Select an action:"
    )


def build_stats_text():
    uptime = datetime.now() - BOT_START_TIME
    h, rem = divmod(int(uptime.total_seconds()), 3600)
    m, _ = divmod(rem, 60)
    last_bc = last_broadcast_time.strftime("%d %b %Y %H:%M") if last_broadcast_time else "Never"
    group_lines = "\n".join(f"  • {g['name']}" for g in GROUPS)
    return (
        "📊 <b>Bot Statistics</b>\n\n"
        f"⏱ <b>Uptime:</b> {h}h {m}m\n"
        f"👥 <b>Groups:</b> {len(GROUPS)}\n"
        f"📢 <b>Last Broadcast:</b> {last_bc}\n\n"
        f"<b>Managed Groups:</b>\n{group_lines}"
    )


def build_groups_text():
    lines = [
        f"{i+1}. <b>{g['name']}</b>\n   ID: <code>{g['id']}</code>"
        for i, g in enumerate(GROUPS)
    ]
    return "📋 <b>Configured Groups:</b>\n\n" + "\n\n".join(lines)


# ─── Update handler ───────────────────────────────────────────────────────────

def handle_update(update):
    global last_broadcast_time

    # ── Callback queries ─────────────────────────────────────────────────────
    if update.get("callback_query"):
        cb = update["callback_query"]
        data = cb.get("data", "")
        chat_id = cb["message"]["chat"]["id"]
        user_id = cb["from"]["id"]
        cb_id = cb["id"]

        # Non-admin: silently dismiss — no error shown
        if user_id != ADMIN_ID:
            answer_callback_query(cb_id)
            return

        if data == "test":
            send_message(chat_id, "✅ DedSeg Main Bot is online and ready.")
            answer_callback_query(cb_id, "✅ Online!")
            return

        if data == "stats":
            send_message(chat_id, build_stats_text(), reply_markup=ADMIN_MENU_INLINE)
            answer_callback_query(cb_id)
            return

        if data == "list_groups":
            send_message(chat_id, build_groups_text(), reply_markup=ADMIN_MENU_INLINE)
            answer_callback_query(cb_id)
            return

        if data == "menu":
            send_message(chat_id, build_admin_menu_text(), reply_markup=ADMIN_MENU_INLINE)
            answer_callback_query(cb_id)
            return

        if data == "broadcast_all":
            send_message(
                chat_id,
                "✉️ <b>Broadcast All</b> mode active.\n"
                "Send your message now. Use /cancel to stop.",
                reply_markup=CANCEL_INLINE,
            )
            set_pending_action(user_id, {"action": "broadcast_all"})
            answer_callback_query(cb_id, "Send your message now.")
            return

        if data == "broadcast_group":
            buttons = [
                [{"text": g["name"], "callback_data": f"select_group|{g['id']}"}]
                for g in GROUPS
            ]
            buttons.append([{"text": "❌ Cancel", "callback_data": "cancel"}])
            send_message(chat_id, "📌 Select a group:", reply_markup={"inline_keyboard": buttons})
            answer_callback_query(cb_id)
            return

        if data == "message_user":
            send_message(
                chat_id,
                "👤 Send the target user ID (numbers only). Use /cancel to stop.",
                reply_markup=CANCEL_INLINE,
            )
            set_pending_action(user_id, {"action": "message_user_id"})
            answer_callback_query(cb_id, "Send the target user ID.")
            return

        if data == "cancel":
            clear_pending_action(user_id)
            send_message(chat_id, "✅ Action cancelled.", reply_markup=ADMIN_MENU_INLINE)
            answer_callback_query(cb_id)
            return

        if data.startswith("select_group|"):
            group_id = data.split("|", 1)[1]
            group_name = GROUP_MAP.get(group_id, group_id)
            send_message(
                chat_id,
                f"✉️ Broadcasting to <b>{group_name}</b>.\n"
                "Send messages now. Use /cancel to stop.",
                reply_markup=CANCEL_INLINE,
            )
            set_pending_action(user_id, {"action": "broadcast_group", "group_id": group_id})
            answer_callback_query(cb_id, f"Selected: {group_name}")
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

    # ── Non-admin private chat: Livegram mode ────────────────────────────────
    if chat_type == "private" and user_id != ADMIN_ID:
        if text.startswith("/start"):
            send_message(
                chat_id,
                f"👋 Hi <b>{first_name}</b>! Welcome to <b>DedSeg</b>.\n\n"
                "📩 Feel free to send us a message and our team will get back to you.\n"
                "🎯 Stay tuned for daily quizzes, facts and motivation in our channels!",
            )
            return
        # Forward any text to admin silently (no error to user)
        if text and not text.startswith("/"):
            user_tag = f"@{username}" if username else f"ID: {user_id}"
            send_message(
                ADMIN_ID,
                f"📩 <b>Message from {first_name}</b> ({user_tag})\n"
                f"🆔 User ID: <code>{user_id}</code>\n\n"
                f"{text}",
            )
        # All other commands from non-admin: silently ignored
        return

    # ── Non-private chat (groups): only admin commands work ──────────────────
    if user_id != ADMIN_ID:
        return

    # ── Admin pending action ─────────────────────────────────────────────────
    pending = get_pending_action(user_id)
    if pending:
        if text.lower().startswith("/cancel"):
            clear_pending_action(user_id)
            send_message(chat_id, "✅ Action cancelled.", reply_markup=ADMIN_MENU_INLINE)
            return

        if pending["action"] == "broadcast_all":
            results = broadcast_message(text)
            last_broadcast_time = datetime.now()
            ok = sum(1 for r in results if r.get("response", {}).get("ok"))
            send_message(
                chat_id,
                f"✅ Broadcast sent to <b>{ok}/{len(results)}</b> groups.\n"
                "Continue sending or use /cancel.",
                reply_markup=CANCEL_INLINE,
            )
            return

        if pending["action"] == "broadcast_group":
            target_id = pending.get("group_id")
            group_name = GROUP_MAP.get(target_id, target_id)
            broadcast_message(text, target_id=target_id)
            last_broadcast_time = datetime.now()
            send_message(
                chat_id,
                f"✅ Sent to <b>{group_name}</b>.\nContinue sending or use /cancel.",
                reply_markup=CANCEL_INLINE,
            )
            return

        if pending["action"] == "message_user_id":
            if not (text.isdigit() or text.startswith("@")):
                send_message(chat_id, "❌ Invalid. Send a numeric user ID or @username, or /cancel.")
                return
            set_pending_action(user_id, {"action": "message_user", "user_id": text})
            send_message(
                chat_id,
                f"👤 Target set: <b>{text}</b>\nSend the message now. Use /cancel to stop.",
                reply_markup=CANCEL_INLINE,
            )
            return

        if pending["action"] == "message_user":
            target_id = pending.get("user_id")
            result = send_message(target_id, f"📩 <b>Message from DedSeg:</b>\n\n{text}")
            if result.get("ok"):
                send_message(
                    chat_id,
                    f"✅ Message sent to <b>{target_id}</b>.\nContinue or use /cancel.",
                    reply_markup=CANCEL_INLINE,
                )
            else:
                send_message(chat_id, f"❌ Failed: {result.get('description', 'unknown error')}")
            return

    # ── Admin commands ────────────────────────────────────────────────────────
    cmd = text.split()[0].lower() if text else ""

    if cmd in ("/start", "/menu", "/help"):
        send_message(chat_id, build_admin_menu_text(), reply_markup=ADMIN_MENU_INLINE)
        return

    if cmd == "/test":
        send_message(chat_id, "✅ DedSeg Main Bot is online and ready.")
        return

    if cmd == "/stats":
        send_message(chat_id, build_stats_text(), reply_markup=ADMIN_MENU_INLINE)
        return

    if cmd == "/reply":
        # /reply <user_id> <message>
        parts = text.split(" ", 2)
        if len(parts) < 3:
            send_message(chat_id, "Usage: /reply &lt;user_id&gt; &lt;your message&gt;")
            return
        target_id, reply_text = parts[1], parts[2]
        result = send_message(target_id, f"📩 <b>DedSeg Team:</b>\n\n{reply_text}")
        if result.get("ok"):
            send_message(chat_id, f"✅ Reply sent to <code>{target_id}</code>.")
        else:
            send_message(chat_id, f"❌ Failed: {result.get('description', 'unknown error')}")
        return

    if cmd == "/broadcast":
        parts = text.split(" ", 1)
        if len(parts) < 2 or not parts[1].strip():
            send_message(chat_id, "Usage: /broadcast &lt;your message&gt;")
            return
        results = broadcast_message(parts[1].strip())
        last_broadcast_time = datetime.now()
        ok = sum(1 for r in results if r.get("response", {}).get("ok"))
        send_message(chat_id, f"✅ Broadcast sent to <b>{ok}/{len(results)}</b> groups.")
        return

    if cmd == "/cancel":
        clear_pending_action(user_id)
        send_message(chat_id, "✅ Action cancelled.", reply_markup=ADMIN_MENU_INLINE)
        return

    # Unknown command (admin only sees this)
    send_message(chat_id, "⚠️ Unknown command. Use /menu to see options.", reply_markup=ADMIN_MENU_INLINE)


# ─── Entry point ──────────────────────────────────────────────────────────────

def run_main_bot():
    print("🚀 DedSeg Main Bot starting...")
    set_my_commands()
    offset = load_offset()
    print("✅ DedSeg Main Bot is running.")

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
            print(f"[main_bot] Network error: {exc}")
            time.sleep(5)
        except Exception as exc:
            print(f"[main_bot] Error: {exc}")
            time.sleep(5)


if __name__ == "__main__":
    run_main_bot()
