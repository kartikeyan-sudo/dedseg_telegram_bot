import requests
from quiz_config import BOT_TOKEN, QUIZ_CHAT_ID

def send_motivation():
    response = requests.get(
        "https://zenquotes.io/api/random"
    )
    data = response.json()[0]
    quote = data["q"]
    author = data["a"]
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": QUIZ_CHAT_ID,
            "text": (
                f"🔥 DAILY MOTIVATION\n\n"
                f"“{quote}”\n\n"
                f"— {author}"
            )
        }
    )
