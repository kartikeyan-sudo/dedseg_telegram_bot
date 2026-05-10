import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8344646379:AAG48jOmfXB4XDEh6zwVZ_fFDfTqFyPdTA0")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "5359923752"))

GROUPS = [
    {"id": os.environ.get("GROUP_1_ID", "-1003922270132"), "name": "DedSeg x Media"},
    {"id": os.environ.get("GROUP_2_ID", "-1003999915272"), "name": "DedSeg x Money"},
    {"id": os.environ.get("GROUP_3_ID", "-1003990925982"), "name": "DedSeg_GC"},
    {"id": os.environ.get("GROUP_4_ID", "-1003852211310"), "name": "DedSeg x EduHub"},
    {"id": os.environ.get("GROUP_5_ID", "-1003969505728"), "name": "Daily Static GK"},
]
