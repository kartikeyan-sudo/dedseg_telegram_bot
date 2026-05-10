from apscheduler.schedulers.background import BackgroundScheduler

from DedSegBot.quiz import send_daily_quiz
from DedSegBot.motivation import send_motivation
from DedSegBot.facts import send_daily_fact

scheduler = BackgroundScheduler()

# 8 AM Quiz
scheduler.add_job(
    send_daily_quiz,
    'cron',
    hour=8,
    minute=0
)

# 1 PM Fact
scheduler.add_job(
    send_daily_fact,
    'cron',
    hour=13,
    minute=0
)

# 9 PM Motivation
scheduler.add_job(
    send_motivation,
    'cron',
    hour=21,
    minute=0
)

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
