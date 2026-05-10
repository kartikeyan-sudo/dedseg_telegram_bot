from fastapi import FastAPI

from DedSegBot.quiz import send_daily_quiz

app = FastAPI()

@app.get("/")
def home():

    return {
        "status": "DedSeg Backend Running"
    }
