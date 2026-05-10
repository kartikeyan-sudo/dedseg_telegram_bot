import sys
import os
import requests

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from DedSegBot.quiz import fetch_questions, send_quick_quiz, send_message
from DedSegBot.quiz_config import BOT_TOKEN, QUIZ_CHAT_ID

def run_test():
    print(f"Starting Local API Check...")
    print(f"Bot Token: {BOT_TOKEN[:8]}...{BOT_TOKEN[-4:]}")
    print(f"Target Chat: {QUIZ_CHAT_ID}")

    # Step 1: Check OpenTDB API directly
    print("\n[1/4] Checking OpenTDB API...")
    questions = fetch_questions(9, amount=1)
    if questions:
        print(f"OpenTDB OK! Fetched: {questions[0]['question'][:50]}...")
    else:
        print("OpenTDB Failed or Rate Limited.")

    # Step 2: Send Dummy Message to Channel
    print("\n[2/4] Sending Dummy Message to Channel...")
    try:
        res = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": QUIZ_CHAT_ID, "text": "Local Test: Bot is communicating with channel successfully!"},
            timeout=10
        )
        print(f"Response: {res.text}")
    except Exception as e:
        print(f"Error: {e}")

    # Step 3: Trigger Quick Quiz
    print("\n[3/4] Sending Quick Quiz Poll...")
    send_quick_quiz()

    print("\nLocal checks complete.")

if __name__ == "__main__":
    run_test()
