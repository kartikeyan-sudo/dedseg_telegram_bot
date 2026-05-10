import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI

from DedSegBot.quiz import send_daily_quiz
from DedSegBot.facts import send_daily_fact
from DedSegBot.motivation import send_motivation
from run import start_bots, wait_for_lock

def background_bot_launcher():
    """Waits for the lock and starts bots without blocking the main web process."""
    lock = wait_for_lock(timeout=120)  # Wait up to 2 mins for deploy transition
    if lock:
        # Keep reference to lock so it's not GC'd
        threading.current_thread().lock = lock
        start_bots()
    else:
        print("⚠️ [FastAPI] Could not acquire bot lock after timeout.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Launch bots in a non-blocking background thread
    threading.Thread(target=background_bot_launcher, daemon=True).start()
    yield

app = FastAPI(lifespan=lifespan)


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
def motivation():

    send_motivation()

    return {
        "message": "Motivation sent successfully"
    }
