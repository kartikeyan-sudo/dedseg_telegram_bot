import requests
from config import BOT_TOKEN, GROUPS


def broadcast_message(message, target_id=None, parse_mode="HTML"):
    """
    Broadcast a message to all configured groups or a specific group.
    Returns a list of result dicts with chat_id, status_code, and response.
    """
    target_groups = GROUPS
    if target_id is not None:
        target_groups = [g for g in GROUPS if g["id"] == target_id]

    results = []
    seen = set()

    for group in target_groups:
        chat_id = group["id"]
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

            result = {"chat_id": chat_id, "status_code": r.status_code, "response": data}
            print(f"[broadcast] {group['name']}: ok={data.get('ok')}")

        except Exception as e:
            print(f"[broadcast] error for {chat_id}: {e}")
            result = {"chat_id": chat_id, "status_code": 0, "response": {"ok": False, "description": str(e)}}

        results.append(result)

    return results
