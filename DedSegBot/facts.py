import requests
from quiz_config import BOT_TOKEN, QUIZ_CHAT_ID

def send_daily_fact():
    response = requests.get(
        "http://numbersapi.com/random/trivia"
    )
    fact = response.text
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": QUIZ_CHAT_ID,
            "text": (
                f"\ud83e\udde0 DAILY GK FACT\n\n"
                f"{fact}"
            )
        }
    )
