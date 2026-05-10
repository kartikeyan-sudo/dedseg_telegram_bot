import requests
from DedSegBot.quiz_config import BOT_TOKEN, QUIZ_CHAT_ID


def send_daily_fact(target_id=None):
    chat_id = target_id or QUIZ_CHAT_ID
    try:
        r = requests.get("http://numbersapi.com/random/trivia", timeout=15)
        r.raise_for_status()
        fact = r.text.strip()
    except Exception as e:
        print(f"[facts] error fetching fact: {e}")
        fact = "Did you know? Every day is a new opportunity to learn something amazing!"

    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": f"🧠 DAILY GK FACT\n\n{fact}",
            },
            timeout=15,
        )
        print(f"[facts] Telegram response: {r.text}")
    except Exception as e:
        print(f"[facts] error sending fact: {e}")
