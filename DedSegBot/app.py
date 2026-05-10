from fastapi import FastAPI
from DedSegBot.quiz import send_daily_quiz
from DedSegBot.facts import send_daily_fact
from DedSegBot.motivation import send_motivation

app = FastAPI()

@app.get("/")
def home():

    return {
        "status": "DedSeg Backend Running"
    }

@app.get("/run-quiz")
def run_quiz():

    send_daily_quiz()

    return {
        "message": "Quiz sent successfully"
    }

@app.get("/send-fact")
def send_fact():

    send_daily_fact()

    return {
        "message": "Fact sent successfully"
    }

@app.get("/send-motivation")
def send_motivation_api():

    send_motivation()

    return {
        "message": "Motivation sent successfully"
    }