import json
import os
import sys
import time
import threading
import requests
from datetime import datetime
from DedSegBot.quiz import send_daily_quiz, send_quick_quiz
from DedSegBot.facts import send_daily_fact
from DedSegBot.motivation import send_motivation
from DedSegBot.broadcast import broadcast_message, copy_message_to_groups
from DedSegBot.config import BOT_TOKEN, ADMIN_ID, GROUPS as STATIC_GROUPS

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
OFFSET_FILE = os.path.join(os.path.dirname(__file__), "update_offset.txt")
DYNAMIC_GROUPS_FILE = os.path.join(os.path.dirname(__file__), "groups.json")

BOT_START_TIME = datetime.now()
last_broadcast_time = None
pending_actions = {}


# ─── Dynamic group management ─────────────────────────────────────────────────

def load_dynamic_groups():
    try:
        with open(DYNAMIC_GROUPS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_dynamic_groups(groups):
    try:
        with open(DYNAMIC_GROUPS_FILE, "w", encoding="utf-8") as f:
            json.dump(groups, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[save_dynamic_groups] error: {e}")


def get_all_groups():
    """Merge static groups (config.py) with dynamically added groups."""
    dynamic = load_dynamic_groups()
    static_ids = {str(g["id"]) for g in STATIC_GROUPS}
    merged = list(STATIC_GROUPS)
    for g in dynamic:
        if str(g["id"]) not in static_ids:
            merged.append(g)
    return merged


def get_group_map():
    return {str(g["id"]): g["name"] for g in get_all_groups()}


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


def copy_message(from_chat_id, message_id, to_chat_id):
    """Copy any message type (text/photo/video/doc/sticker/voice/etc.) to a chat."""
    try:
        r = requests.post(
            f"{BASE_URL}/copyMessage",
            json={
                "chat_id": to_chat_id,
                "from_chat_id": from_chat_id,
                "message_id": message_id,
            },
            timeout=15,
        )
        return r.json()
    except Exception as e:
        print(f"[copy_message] error: {e}")
        return {}


def get_chat(chat_id):
    """Fetch chat info from Telegram to get the group name."""
    try:
        r = requests.post(f"{BASE_URL}/getChat", json={"chat_id": chat_id}, timeout=10)
        return r.json()
    except Exception as e:
        print(f"[get_chat] error: {e}")
        return {}


def has_media(message):
    """Returns True if the message contains any non-text media."""
    media_keys = ("photo", "video", "document", "audio", "voice",
                  "sticker", "animation", "video_note", "contact", "location")
    return any(message.get(k) for k in media_keys)


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


# ─── Keyboards ────────────────────────────────────────────────────────────────

ADMIN_MENU_INLINE = {
    "inline_keyboard": [
        [
            {"text": "🔔 Broadcast All",   "callback_data": "broadcast_all"},
            {"text": "📌 Broadcast Group", "callback_data": "broadcast_group"},
        ],
        [
            {"text": "👤 Message User",  "callback_data": "message_user"},
            {"text": "📊 Stats",         "callback_data": "stats"},
        ],
        [
            {"text": "📋 List Groups",  "callback_data": "list_groups"},
            {"text": "➕ Add Group",    "callback_data": "add_group"},
        ],
        [
            {"text": "📚 Send Full Quiz Set", "callback_data": "run_quiz"},
        ],
        [
            {"text": "🔥 Send Quote to Channel", "callback_data": "run_quote"},
            {"text": "🧠 Send Fact to Channel", "callback_data": "run_fact"},
        ],
        [
            {"text": "🧪 Quick API Test Quiz", "callback_data": "run_test"},
            {"text": "❌ Cancel Action", "callback_data": "cancel"},
        ],
    ]
}

CANCEL_INLINE = {
    "inline_keyboard": [
        [{"text": "❌ Cancel", "callback_data": "cancel"}]
    ]
}


# ─── Scoped commands ──────────────────────────────────────────────────────────

def set_my_commands():
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
        requests.post(f"{BASE_URL}/setMyCommands", json={
            "commands": admin_cmds,
            "scope": {"type": "chat", "chat_id": ADMIN_ID},
        }, timeout=10)
        requests.post(f"{BASE_URL}/setMyCommands", json={
            "commands": [],
            "scope": {"type": "all_private_chats"},
        }, timeout=10)
        print("[main_bot] Commands scoped to admin only.")
    except Exception as e:
        print(f"[set_my_commands] error: {e}")


# ─── Text builders ─────────────────────────────────────────────────────────────

def build_admin_menu_text():
    uptime = datetime.now() - BOT_START_TIME
    h, rem = divmod(int(uptime.total_seconds()), 3600)
    m, _ = divmod(rem, 60)
    all_groups = get_all_groups()
    return (
        "🎛 <b>DedSeg Admin Panel</b>\n"
        f"⏱ Uptime: {h}h {m}m  |  👥 Groups: {len(all_groups)}\n\n"
        "Select an action:"
    )


def build_stats_text():
    uptime = datetime.now() - BOT_START_TIME
    h, rem = divmod(int(uptime.total_seconds()), 3600)
    m, _ = divmod(rem, 60)
    last_bc = last_broadcast_time.strftime("%d %b %Y %H:%M") if last_broadcast_time else "Never"
    all_groups = get_all_groups()
    group_lines = "\n".join(f"  • {g['name']}" for g in all_groups)
    return (
        "📊 <b>Bot Statistics</b>\n\n"
        f"⏱ <b>Uptime:</b> {h}h {m}m\n"
        f"👥 <b>Groups:</b> {len(all_groups)}\n"
        f"📢 <b>Last Broadcast:</b> {last_bc}\n\n"
        f"<b>Managed Groups:</b>\n{group_lines}"
    )


def build_groups_text():
    all_groups = get_all_groups()
    lines = [
        f"{i+1}. <b>{g['name']}</b>\n   ID: <code>{g['id']}</code>"
        for i, g in enumerate(all_groups)
    ]
    return "📋 <b>All Configured Groups:</b>\n\n" + "\n\n".join(lines)


# ─── Broadcast helpers ────────────────────────────────────────────────────────

def do_broadcast(chat_id, message_id, message_text, target_id=None):
    """
    Broadcast to groups. Uses copyMessage for media, sendMessage for plain text.
    Returns (ok_count, total_count).
    """
    global last_broadcast_time
    all_groups = get_all_groups()

    if message_text:
        # Plain text — use sendMessage (supports HTML parse_mode)
        results = broadcast_message(message_text, target_id=target_id, groups=all_groups)
    else:
        # Media — use copyMessage to preserve all media types
        results = copy_message_to_groups(
            from_chat_id=chat_id,
            message_id=message_id,
            bot_token=BOT_TOKEN,
            target_id=target_id,
            groups=all_groups,
        )

    last_broadcast_time = datetime.now()
    ok = sum(1 for r in results if r.get("response", {}).get("ok"))
    return ok, len(results)


# ─── Update handler ───────────────────────────────────────────────────────────

def handle_update(update):
    # ── Callback queries ─────────────────────────────────────────────────────
    if update.get("callback_query"):
        cb = update["callback_query"]
        data = cb.get("data", "")
        chat_id = cb["message"]["chat"]["id"]
        user_id = cb["from"]["id"]
        cb_id = cb["id"]

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

        if data == "add_group":
            send_message(
                chat_id,
                "➕ <b>Add New Group</b>\n\n"
                "Send the group's <b>Chat ID</b> (e.g. <code>-1001234567890</code>)\n\n"
                "💡 <i>Tip: Forward any message from the group here, or send the ID directly.\n"
                "To get a group ID, add @userinfobot to the group temporarily.</i>\n\n"
                "Use /cancel to abort.",
                reply_markup=CANCEL_INLINE,
            )
            set_pending_action(user_id, {"action": "add_group"})
            answer_callback_query(cb_id, "Send the group chat ID.")
            return

        if data == "menu":
            send_message(chat_id, build_admin_menu_text(), reply_markup=ADMIN_MENU_INLINE)
            answer_callback_query(cb_id)
            return

        if data == "broadcast_all":
            send_message(
                chat_id,
                "✉️ <b>Broadcast All</b> mode active.\n\n"
                "Send any message now — text, photo, video, document, voice, sticker, etc.\n"
                "Use /cancel to stop.",
                reply_markup=CANCEL_INLINE,
            )
            set_pending_action(user_id, {"action": "broadcast_all"})
            answer_callback_query(cb_id, "Send your message now.")
            return

        if data == "broadcast_group":
            all_groups = get_all_groups()
            buttons = [
                [{"text": g["name"], "callback_data": f"select_group|{g['id']}"}]
                for g in all_groups
            ]
            buttons.append([{"text": "❌ Cancel", "callback_data": "cancel"}])
            send_message(chat_id, "📌 Select a group to broadcast to:", reply_markup={"inline_keyboard": buttons})
            answer_callback_query(cb_id)
            return

        if data == "message_user":
            send_message(
                chat_id,
                "👤 <b>Message User</b>\n\nSend the target user's numeric ID.\nUse /cancel to stop.",
                reply_markup=CANCEL_INLINE,
            )
            set_pending_action(user_id, {"action": "message_user_id"})
            answer_callback_query(cb_id, "Send the target user ID.")
            return

        if data == "run_quiz":
            send_message(chat_id, "⏳ Sending full quiz set to channel...")
            threading.Thread(target=send_daily_quiz, daemon=True).start()
            answer_callback_query(cb_id, "✅ Quiz started!")
            return

        if data == "run_quote":
            send_message(chat_id, "⏳ Sending daily quote to channel...")
            threading.Thread(target=send_motivation, daemon=True).start()
            answer_callback_query(cb_id, "✅ Quote sent!")
            return

        if data == "run_fact":
            send_message(chat_id, "⏳ Sending GK fact to channel...")
            threading.Thread(target=send_daily_fact, daemon=True).start()
            answer_callback_query(cb_id, "✅ Fact sent!")
            return

        if data == "run_test":
            send_message(chat_id, "⏳ Running quick API test quiz in this chat...")
            threading.Thread(target=send_quick_quiz, args=(chat_id,), daemon=True).start()
            answer_callback_query(cb_id, "✅ Test quiz sent!")
            return

        if data == "cancel":
            clear_pending_action(user_id)
            send_message(chat_id, "✅ Action cancelled.", reply_markup=ADMIN_MENU_INLINE)
            answer_callback_query(cb_id)
            return

        if data.startswith("select_group|"):
            group_id = data.split("|", 1)[1]
            group_name = get_group_map().get(group_id, group_id)
            send_message(
                chat_id,
                f"✉️ Broadcasting to <b>{group_name}</b>.\n\n"
                "Send any message — text, photo, video, document, voice, sticker, etc.\n"
                "Use /cancel to stop.",
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
    message_id = message["message_id"]

    # ── Non-admin private chat: Livegram mode ─────────────────────────────────
    if chat_type == "private" and user_id != ADMIN_ID:
        if text.startswith("/start"):
            send_message(
                chat_id,
                f"👋 Hi <b>{first_name}</b>! Welcome to <b>DedSeg</b>.\n\n"
                "📩 Feel free to send us a message and our team will get back to you.\n"
                "🎯 Stay tuned for daily quizzes, facts and motivation in our channels!",
            )
            return
        # Forward any content (text or media) to admin
        if text or has_media(message):
            user_tag = f"@{username}" if username else f"ID: {user_id}"
            if text and not has_media(message):
                # Text-only: embed message in the header — admin sees ONE message
                send_message(
                    ADMIN_ID,
                    f"💬 <b>{first_name}</b> ({user_tag})\n"
                    f"🆔 <code>{user_id}</code>  |  /reply {user_id} &lt;msg&gt;\n\n"
                    f"{text}",
                )
            else:
                # Media: send compact header, then copy the media — 2 messages (unavoidable)
                send_message(
                    ADMIN_ID,
                    f"📎 <b>{first_name}</b> ({user_tag}) sent media\n"
                    f"🆔 <code>{user_id}</code>  |  /reply {user_id} &lt;msg&gt;",
                )
                copy_message(from_chat_id=chat_id, message_id=message_id, to_chat_id=ADMIN_ID)
        return

    # ── Command Triggers (Public in Groups, Admin-only in DM) ─────────────────
    cmd = text.split()[0].lower() if text else ""
    is_admin = (user_id == ADMIN_ID)

    if cmd == "/motivation":
        send_message(chat_id, "⏳ Sending motivation...")
        threading.Thread(target=send_motivation, args=(chat_id,), daemon=True).start()
        return

    if cmd in ("/fact", "/oneliner"):
        send_message(chat_id, "⏳ Sending one-liner...")
        threading.Thread(target=send_daily_fact, args=(chat_id,), daemon=True).start()
        return

    if cmd == "/quiz":
        # Quizzes are long; keep them admin-only to avoid spam
        if not is_admin:
            send_message(chat_id, "⚠️ Only admins can trigger a full quiz set.")
            return
        send_message(chat_id, "⏳ Starting quiz in background...")
        threading.Thread(target=send_daily_quiz, args=(chat_id,), daemon=True).start()
        return

    # ── Non-admin non-private: ignore rest ───────────────────────────────────
    if not is_admin:
        return

    # ── Admin pending action ──────────────────────────────────────────────────
    pending = get_pending_action(user_id)
    if pending:
        if text.lower().startswith("/cancel"):
            clear_pending_action(user_id)
            send_message(chat_id, "✅ Action cancelled.", reply_markup=ADMIN_MENU_INLINE)
            return

        # ── Add Group ──
        if pending["action"] == "add_group":
            # Try to detect group ID from forwarded message or raw text
            forwarded_chat = message.get("forward_from_chat", {})
            if forwarded_chat:
                group_id = str(forwarded_chat.get("id", ""))
                group_name = forwarded_chat.get("title", group_id)
            elif text.lstrip("-").isdigit():
                group_id = text.strip()
                # Look up the name via getChat
                info = get_chat(group_id)
                if info.get("ok"):
                    group_name = info["result"].get("title", group_id)
                else:
                    send_message(
                        chat_id,
                        f"❌ Could not find that group. Make sure:\n"
                        "• The bot is a member of the group\n"
                        "• The ID is correct (starts with <code>-100...</code>)\n\n"
                        f"Error: <code>{info.get('description', 'Unknown')}</code>",
                        reply_markup=CANCEL_INLINE,
                    )
                    return
            else:
                send_message(
                    chat_id,
                    "❌ Invalid input. Send a numeric group ID like <code>-1001234567890</code> "
                    "or forward a message from the group. Use /cancel to abort.",
                    reply_markup=CANCEL_INLINE,
                )
                return

            # Check if already in the list
            all_groups = get_all_groups()
            existing_ids = {str(g["id"]) for g in all_groups}
            if group_id in existing_ids:
                send_message(
                    chat_id,
                    f"⚠️ Group <b>{group_name}</b> (<code>{group_id}</code>) is already in the list.",
                    reply_markup=ADMIN_MENU_INLINE,
                )
                clear_pending_action(user_id)
                return

            # Add to dynamic groups
            dynamic = load_dynamic_groups()
            dynamic.append({"id": group_id, "name": group_name})
            save_dynamic_groups(dynamic)
            clear_pending_action(user_id)

            send_message(
                chat_id,
                f"✅ <b>Group added successfully!</b>\n\n"
                f"📌 <b>{group_name}</b>\n"
                f"🆔 <code>{group_id}</code>\n\n"
                f"Total groups now: <b>{len(get_all_groups())}</b>",
                reply_markup=ADMIN_MENU_INLINE,
            )
            return

        # ── Broadcast All ──
        if pending["action"] == "broadcast_all":
            msg_text = text if not has_media(message) else None
            ok, total = do_broadcast(chat_id, message_id, msg_text)
            send_message(
                chat_id,
                f"✅ Broadcast sent to <b>{ok}/{total}</b> groups.\n"
                "Continue sending or use /cancel.",
                reply_markup=CANCEL_INLINE,
            )
            return

        # ── Broadcast Group ──
        if pending["action"] == "broadcast_group":
            target_id = pending.get("group_id")
            group_name = get_group_map().get(target_id, target_id)
            msg_text = text if not has_media(message) else None
            ok, total = do_broadcast(chat_id, message_id, msg_text, target_id=target_id)
            send_message(
                chat_id,
                f"✅ Sent to <b>{group_name}</b>.\nContinue sending or use /cancel.",
                reply_markup=CANCEL_INLINE,
            )
            return

        # ── Message User (step 1: get user ID) ──
        if pending["action"] == "message_user_id":
            if not (text.isdigit() or text.startswith("@")):
                send_message(chat_id, "❌ Invalid. Send a numeric user ID or @username, or /cancel.")
                return
            set_pending_action(user_id, {"action": "message_user", "user_id": text})
            send_message(
                chat_id,
                f"👤 Target set: <b>{text}</b>\n\n"
                "Now send any message — text, photo, video, doc, voice, sticker, etc.\n"
                "Use /cancel to stop.",
                reply_markup=CANCEL_INLINE,
            )
            return

        # ── Message User (step 2: send the content) ──
        if pending["action"] == "message_user":
            target_id = pending.get("user_id")
            target_name = pending.get("user_name", target_id)
            # Use copyMessage for ALL content types — no prefix, raw message delivered cleanly
            result = copy_message(from_chat_id=chat_id, message_id=message_id, to_chat_id=target_id)

            if result.get("ok"):
                send_message(
                    chat_id,
                    f"✅ Message delivered to <b>{target_name}</b> (<code>{target_id}</code>).\n"
                    "Continue sending or use /cancel.",
                    reply_markup=CANCEL_INLINE,
                )
            else:
                send_message(
                    chat_id,
                    f"❌ Failed to send: <code>{result.get('description', 'unknown error')}</code>",
                    reply_markup=CANCEL_INLINE,
                )
            return

    # ── Admin commands (no pending action) ───────────────────────────────────
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
        # /reply <user_id> <message text>
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
        ok, total = do_broadcast(chat_id, message_id, parts[1].strip())
        send_message(chat_id, f"✅ Broadcast sent to <b>{ok}/{total}</b> groups.")
        return


    if cmd == "/cancel":
        clear_pending_action(user_id)
        send_message(chat_id, "✅ Action cancelled.", reply_markup=ADMIN_MENU_INLINE)
        return

    # Unknown command for admin
    send_message(chat_id, "⚠️ Unknown command. Use /menu to see options.", reply_markup=ADMIN_MENU_INLINE)


# ─── Entry point ──────────────────────────────────────────────────────────────

def run_main_bot():
    print("[main_bot] Starting DedSeg Main Bot...")
    set_my_commands()
    offset = load_offset()
    print("[main_bot] Running. Polling for updates...")

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
