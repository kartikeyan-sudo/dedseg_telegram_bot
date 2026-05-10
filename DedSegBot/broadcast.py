import requests
from DedSegBot.config import BOT_TOKEN, GROUPS as STATIC_GROUPS


def broadcast_message(message, target_id=None, parse_mode="HTML", groups=None):
    """
    Send a text message to all configured groups or a specific group.
    Pass `groups` to override the static group list (e.g. with dynamic groups merged in).
    Returns a list of result dicts with chat_id, status_code, and response.
    """
    all_groups = groups if groups is not None else STATIC_GROUPS
    target_groups = all_groups
    if target_id is not None:
        target_groups = [g for g in all_groups if str(g["id"]) == str(target_id)]

    results = []
    seen = set()

    for group in target_groups:
        chat_id = str(group["id"])
        if chat_id in seen:
            continue
        seen.add(chat_id)

        try:
            r = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": parse_mode,
                },
                timeout=15,
            )
            try:
                data = r.json()
            except ValueError:
                data = {"ok": False, "description": "invalid-json", "raw": r.text}

            print(f"[broadcast] {group.get('name', chat_id)}: ok={data.get('ok')}")
            results.append({"chat_id": chat_id, "status_code": r.status_code, "response": data})

        except Exception as e:
            print(f"[broadcast] error for {chat_id}: {e}")
            results.append({"chat_id": chat_id, "status_code": 0, "response": {"ok": False, "description": str(e)}})

    return results


def copy_message_to_groups(from_chat_id, message_id, bot_token, target_id=None, groups=None):
    """
    Use Telegram's copyMessage to forward ANY media type (photo, video, doc, sticker, etc.)
    to all configured groups or a specific group. Preserves captions, media, everything.
    """
    all_groups = groups if groups is not None else STATIC_GROUPS
    target_groups = all_groups
    if target_id is not None:
        target_groups = [g for g in all_groups if str(g["id"]) == str(target_id)]

    results = []
    seen = set()

    for group in target_groups:
        chat_id = str(group["id"])
        if chat_id in seen:
            continue
        seen.add(chat_id)

        try:
            r = requests.post(
                f"https://api.telegram.org/bot{bot_token}/copyMessage",
                json={
                    "chat_id": chat_id,
                    "from_chat_id": from_chat_id,
                    "message_id": message_id,
                },
                timeout=15,
            )
            try:
                data = r.json()
            except ValueError:
                data = {"ok": False, "description": "invalid-json", "raw": r.text}

            print(f"[copy_broadcast] {group.get('name', chat_id)}: ok={data.get('ok')}")
            results.append({"chat_id": chat_id, "status_code": r.status_code, "response": data})

        except Exception as e:
            print(f"[copy_broadcast] error for {chat_id}: {e}")
            results.append({"chat_id": chat_id, "status_code": 0, "response": {"ok": False, "description": str(e)}})

    return results
