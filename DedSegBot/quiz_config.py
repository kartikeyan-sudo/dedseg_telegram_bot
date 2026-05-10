import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("QUIZ_BOT_TOKEN") or os.environ.get("BOT_TOKEN", "8689285250:AAHtee6QMjUjJiA-jJ6YMfiTFIvQv6SKlvE")
QUIZ_CHAT_ID = os.environ.get("QUIZ_CHAT_ID", "-1003969505728")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "5359923752"))
