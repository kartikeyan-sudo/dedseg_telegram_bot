import sys
import os
import requests

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from DedSegBot.quiz import send_daily_quiz
from DedSegBot.quiz_config import BOT_TOKEN, QUIZ_CHAT_ID

def run_full_quiz():
    print(f"Triggering Full Quiz for Channel: {QUIZ_CHAT_ID}...")
    try:
        # This will take a while as it fetches and translates multiple categories
        send_daily_quiz()
        print("Done!")
    except Exception as e:
        # Ignore the emoji print error for this test
        print(f"Finished with potential print error: {e}")

if __name__ == "__main__":
    run_full_quiz()
