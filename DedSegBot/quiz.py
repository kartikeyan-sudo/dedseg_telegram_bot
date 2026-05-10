import requests
import random
import html
import time
from deep_translator import GoogleTranslator
from quiz_config import BOT_TOKEN, QUIZ_CHAT_ID

categories = {
    "📘 General Knowledge": 9,
    "🔬 Science & Nature": 17,
    "🌍 Geography": 22,
    "🏛 History": 23,
    "⚖ Politics": 24
}


def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": QUIZ_CHAT_ID,
        "text": text
    }
    response = requests.post(url, json=payload)
    print(response.text)


def send_poll(question, options, correct_index, explanation):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPoll"
    payload = {
        "chat_id": QUIZ_CHAT_ID,
        "question": question[:250],
        "options": options,
        "type": "quiz",
        "correct_option_id": correct_index,
        "is_anonymous": True,
        "explanation": explanation[:200]
    }
    response = requests.post(url, json=payload)
    print(response.text)


def translate_to_hindi(text):
    try:
        return GoogleTranslator(source="auto", target="hi").translate(text)
    except Exception as e:
        print("Translation Error:", e)
        return text


def send_daily_quiz():
    send_message(
        "📚 DAILY SSC / UPSC QUIZ SET 🔥\n\n"
        "✅ English + Hindi Questions\n"
        "🎯 Attempt all quizzes carefully!"
    )

    for category_name, category_id in categories.items():
        send_message(
            f"━━━━━━━━━━━━━━━\n{category_name}\n━━━━━━━━━━━━━━━"
        )

        api_url = (
            f"https://opentdb.com/api.php?"
            f"amount=5&category={category_id}&type=multiple"
        )
        response = requests.get(api_url)
        data = response.json()
        questions = data.get("results", [])

        for q in questions:
            english_question = html.unescape(q["question"])
            english_correct = html.unescape(q["correct_answer"])
            english_incorrect = [html.unescape(opt) for opt in q["incorrect_answers"]]

            hindi_question = translate_to_hindi(english_question)
            hindi_correct = translate_to_hindi(english_correct)
            hindi_incorrect = [translate_to_hindi(opt) for opt in english_incorrect]

            english_options = english_incorrect + [english_correct]
            random.shuffle(english_options)
            english_correct_index = english_options.index(english_correct)
            english_options = [opt[:90] for opt in english_options]
            send_poll(
                english_question,
                english_options,
                english_correct_index,
                f"✅ Correct Answer: {english_options[english_correct_index]}"
            )
            time.sleep(2)

            hindi_options = hindi_incorrect + [hindi_correct]
            random.shuffle(hindi_options)
            hindi_correct_index = hindi_options.index(hindi_correct)
            hindi_options = [opt[:90] for opt in hindi_options]
            send_poll(
                hindi_question,
                hindi_options,
                hindi_correct_index,
                f"✅ सही उत्तर: {hindi_options[hindi_correct_index]}"
            )
            time.sleep(2)

    print("✅ English + Hindi SSC/UPSC quizzes sent successfully!")
