import random
import html
import time
import requests
from deep_translator import GoogleTranslator
from DedSegBot.quiz_config import BOT_TOKEN, QUIZ_CHAT_ID

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

CATEGORIES = {
    "📘 General Knowledge": 9,
    "🔬 Science & Nature":  17,
    "🌍 Geography":          22,
    "🏛 History":            23,
    "⚖ Politics":           24,
}


def send_message(text, target_id=None):
    chat_id = target_id or QUIZ_CHAT_ID
    try:
        r = requests.post(
            f"{BASE_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=15,
        )
        print(r.text)
    except Exception as e:
        print(f"[quiz send_message] error: {e}")


def send_poll(question, options, correct_index, explanation, target_id=None):
    chat_id = target_id or QUIZ_CHAT_ID
    try:
        r = requests.post(
            f"{BASE_URL}/sendPoll",
            json={
                "chat_id": chat_id,
                "question": question[:250],
                "options": options,
                "type": "quiz",
                "correct_option_id": correct_index,
                "is_anonymous": True,
                "explanation": explanation[:200],
            },
            timeout=15,
        )
        print(r.text)
    except Exception as e:
        print(f"[send_poll] error: {e}")


def translate_to_hindi(text):
    try:
        return GoogleTranslator(source="auto", target="hi").translate(text)
    except Exception as e:
        print(f"[translate] error: {e}")
        return text


def fetch_questions(category_id, amount=5, retries=3):
    """Fetch questions from OpenTDB with retry on rate limit (response_code 5)."""
    url = f"https://opentdb.com/api.php?amount={amount}&category={category_id}&type=multiple"
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=15)
            data = r.json()
            code = data.get("response_code", -1)
            if code == 0:
                return data.get("results", [])
            if code == 5:
                # Rate limited — wait and retry
                print(f"[fetch_questions] Rate limited, waiting 10s (attempt {attempt+1})")
                time.sleep(10)
                continue
            print(f"[fetch_questions] API response_code={code}")
            return []
        except Exception as e:
            print(f"[fetch_questions] error: {e}")
            time.sleep(5)
    return []


def send_daily_quiz(target_id=None):
    send_message(
        "📚 DAILY SSC / UPSC QUIZ SET 🔥\n\n"
        "✅ English + Hindi Questions\n"
        "🎯 Attempt all quizzes carefully!",
        target_id=target_id
    )

    for category_name, category_id in CATEGORIES.items():
        send_message(f"━━━━━━━━━━━━━━━\n{category_name}\n━━━━━━━━━━━━━━━", target_id=target_id)

        questions = fetch_questions(category_id)
        if not questions:
            send_message(f"⚠️ Could not load questions for {category_name}. Skipping.", target_id=target_id)
            continue

        for q in questions:
            try:
                eng_q = html.unescape(q["question"])
                eng_correct = html.unescape(q["correct_answer"])
                eng_incorrect = [html.unescape(o) for o in q["incorrect_answers"]]

                hi_q = translate_to_hindi(eng_q)
                hi_correct = translate_to_hindi(eng_correct)
                hi_incorrect = [translate_to_hindi(o) for o in eng_incorrect]

                # English poll
                eng_opts = eng_incorrect + [eng_correct]
                random.shuffle(eng_opts)
                eng_idx = eng_opts.index(eng_correct)
                eng_opts = [o[:90] for o in eng_opts]
                send_poll(eng_q, eng_opts, eng_idx, f"✅ Correct Answer: {eng_opts[eng_idx]}", target_id=target_id)
                time.sleep(2)

                # Hindi poll
                hi_opts = hi_incorrect + [hi_correct]
                random.shuffle(hi_opts)
                hi_idx = hi_opts.index(hi_correct)
                hi_opts = [o[:90] for o in hi_opts]
                send_poll(hi_q, hi_opts, hi_idx, f"✅ सही उत्तर: {hi_opts[hi_idx]}", target_id=target_id)
                time.sleep(2)

            except Exception as e:
                print(f"[send_daily_quiz] question error: {e}")
                continue

def send_quick_quiz(target_id=None):
    """Sends a single question to quickly verify API and delivery."""
    send_message("🧪 <b>QUICK API TEST QUIZ</b>", target_id=target_id)
    category_name = "📘 General Knowledge"
    category_id = 9
    
    questions = fetch_questions(category_id, amount=1)
    if not questions:
        send_message("❌ Failed to fetch test question.", target_id=target_id)
        return

    q = questions[0]
    try:
        eng_q = html.unescape(q["question"])
        eng_correct = html.unescape(q["correct_answer"])
        eng_incorrect = [html.unescape(o) for o in q["incorrect_answers"]]

        eng_opts = eng_incorrect + [eng_correct]
        random.shuffle(eng_opts)
        eng_idx = eng_opts.index(eng_correct)
        eng_opts = [o[:90] for o in eng_opts]
        
        send_poll(eng_q, eng_opts, eng_idx, f"✅ Correct Answer: {eng_opts[eng_idx]}", target_id=target_id)
        print("✅ Quick quiz test sent successfully!")
    except Exception as e:
        print(f"[send_quick_quiz] error: {e}")

    print("✅ English + Hindi SSC/UPSC quizzes sent successfully!")
