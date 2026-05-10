import requests
from DedSegBot.quiz_config import BOT_TOKEN, QUIZ_CHAT_ID


def send_daily_fact():
    try:
        r = requests.get("http://numbersapi.com/random/trivia", timeout=15)
        r.raise_for_status()
        fact = r.text.strip()
    except Exception as e:
        print(f"[facts] error fetching fact: {e}")
        fact = "Did you know? Every day is a new opportunity to learn something amazing!"

    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": QUIZ_CHAT_ID,
                "text": f"🧠 DAILY GK FACT\n\n{fact}",
            },
            timeout=15,
        )
    except Exception as e:
        print(f"[facts] error sending fact: {e}")
