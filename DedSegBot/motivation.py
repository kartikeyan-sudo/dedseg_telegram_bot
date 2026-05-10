import requests
from DedSegBot.quiz_config import BOT_TOKEN, QUIZ_CHAT_ID

FALLBACK_QUOTE = (
    '"The secret of getting ahead is getting started."\n\n— Mark Twain'
)


def send_motivation(target_id=None):
    chat_id = target_id or QUIZ_CHAT_ID
    try:
        r = requests.get("https://zenquotes.io/api/random", timeout=15)
        r.raise_for_status()
        data = r.json()
        if not data or not isinstance(data, list):
            raise ValueError("Empty or invalid response")
        quote = data[0].get("q", "").strip()
        author = data[0].get("a", "Unknown").strip()
        text = f"🔥 DAILY MOTIVATION\n\n\"{quote}\"\n\n— {author}"
    except Exception as e:
        print(f"[motivation] error: {e}")
        text = f"🔥 DAILY MOTIVATION\n\n{FALLBACK_QUOTE}"

    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=15,
        )
        print(f"[motivation] Telegram response: {r.text}")
    except Exception as e:
        print(f"[motivation] error sending: {e}")
