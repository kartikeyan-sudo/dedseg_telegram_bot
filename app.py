from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def home():
    return {"status": "running"}


@app.get("/test")
def test():

    try:
        from DedSegBot.quiz import send_daily_quiz

        return {
            "status": "quiz import successful"
        }

    except Exception as e:

        return {
            "error": str(e)
        }
