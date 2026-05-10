import requests
from config import BOT_TOKEN, GROUPS


def broadcast_message(message, target_id=None):
    results = []
    target_groups = GROUPS
    if target_id is not None:
        target_groups = [group for group in GROUPS if group["id"] == target_id]

    seen = set()
    for group in target_groups:
        chat_id = group["id"]
        if chat_id in seen:
            continue
        seen.add(chat_id)
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": message
            }
        )
        try:
            data = response.json()
        except ValueError:
            data = {"ok": False, "error": "invalid-json-response", "text": response.text}
        result = {
            "chat_id": chat_id,
            "status_code": response.status_code,
            "response": data
        }
        print("Broadcast result:", result)
        results.append(result)
    return results
