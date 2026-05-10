import requests
import random
import html
import json
import time
from deep_translator import GoogleTranslator
# ==========================================
# TELEGRAM CONFIG
# ==========================================

BOT_TOKEN = "8689285250:AAHtee6QMjUjJiA-jJ6YMfiTFIvQv6SKlvE"
CHAT_ID = "-1003969505728"



# =====================================================
# SSC / UPSC STYLE CATEGORIES
# =====================================================

categories = {
    "📘 General Knowledge": 9,
    "🔬 Science & Nature": 17,
    "🌍 Geography": 22,
    "🏛 History": 23,
    "⚖ Politics": 24
}

# =====================================================
# TELEGRAM SEND MESSAGE
# =====================================================

def send_message(text):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }

    response = requests.post(url, json=payload)

    print(response.text)

# =====================================================
# TELEGRAM SEND QUIZ POLL
# =====================================================

def send_poll(question, options, correct_index, explanation):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPoll"

    payload = {
        "chat_id": CHAT_ID,
        "question": question[:250],
        "options": options,
        "type": "quiz",
        "correct_option_id": correct_index,
        "is_anonymous": True,
        "explanation": explanation[:200]
    }

    response = requests.post(url, json=payload)

    print(response.text)

# =====================================================
# TRANSLATE ENGLISH → HINDI
# =====================================================

def translate_to_hindi(text):

    try:

        translated = GoogleTranslator(
            source='auto',
            target='hi'
        ).translate(text)

        return translated

    except Exception as e:

        print("Translation Error:", e)

        return text

# =====================================================
# START MESSAGE
# =====================================================

send_message(
    "📚 DAILY SSC / UPSC QUIZ SET 🔥\n\n"
    "✅ English + Hindi Questions\n"
    "🎯 Attempt all quizzes carefully!"
)

# =====================================================
# LOOP THROUGH CATEGORIES
# =====================================================

for category_name, category_id in categories.items():

    # =================================================
    # CATEGORY HEADER
    # =================================================

    send_message(
        f"━━━━━━━━━━━━━━━\n"
        f"{category_name}\n"
        f"━━━━━━━━━━━━━━━"
    )

    # =================================================
    # FETCH 5 QUESTIONS
    # =================================================

    api_url = (
        f"https://opentdb.com/api.php?"
        f"amount=5&category={category_id}&type=multiple"
    )

    response = requests.get(api_url)
    data = response.json()

    questions = data["results"]

    # =================================================
    # SEND QUESTIONS
    # =================================================

    for q in questions:

        # =============================================
        # ENGLISH QUESTION
        # =============================================

        english_question = html.unescape(
            q["question"]
        )

        english_correct = html.unescape(
            q["correct_answer"]
        )

        english_incorrect = [
            html.unescape(opt)
            for opt in q["incorrect_answers"]
        ]

        # =============================================
        # HINDI TRANSLATION
        # =============================================

        hindi_question = translate_to_hindi(
            english_question
        )

        hindi_correct = translate_to_hindi(
            english_correct
        )

        hindi_incorrect = [
            translate_to_hindi(opt)
            for opt in english_incorrect
        ]

        # =============================================
        # CREATE ENGLISH OPTIONS
        # =============================================

        english_options = (
            english_incorrect + [english_correct]
        )

        random.shuffle(english_options)

        english_correct_index = (
            english_options.index(english_correct)
        )

        english_options = [
            opt[:90]
            for opt in english_options
        ]

        # =============================================
        # SEND ENGLISH QUIZ
        # =============================================

        send_poll(
            english_question,
            english_options,
            english_correct_index,
            f"✅ Correct Answer: {english_options[english_correct_index]}"
        )

        time.sleep(2)

        # =============================================
        # CREATE HINDI OPTIONS
        # =============================================

        hindi_options = (
            hindi_incorrect + [hindi_correct]
        )

        random.shuffle(hindi_options)

        hindi_correct_index = (
            hindi_options.index(hindi_correct)
        )

        hindi_options = [
            opt[:90]
            for opt in hindi_options
        ]

        # =============================================
        # SEND HINDI QUIZ
        # =============================================

        send_poll(
            hindi_question,
            hindi_options,
            hindi_correct_index,
            f"✅ सही उत्तर: {hindi_options[hindi_correct_index]}"
        )

        time.sleep(2)

print("✅ English + Hindi SSC/UPSC quizzes sent successfully!")