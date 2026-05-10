# 🎯 DedSeg Telegram Bot Ecosystem

A powerful, scalable Telegram bot ecosystem built for **DedSeg** community engagement with automated quizzes, broadcasts, motivational content, and GK facts.

---

## 📋 Overview

**DedSeg** is a comprehensive Telegram bot system consisting of:

1. **DedSeg Main Bot** — Admin control center for broadcasts, group targeting, and user messaging
2. **Daily Static GK Bot** — Automated daily quiz scheduler with Hindi translations

Both bots are designed with **admin-only access** for secure command execution and production-grade reliability.

---

## ✨ Features

### DedSeg Main Bot
- 🔐 **Admin-Only Access** — Secure command handling with admin ID verification
- 📢 **Smart Broadcasts** — Send messages to all groups or target specific groups
- 👤 **Direct User Messaging** — Send personalized messages to users by ID or username
- 📱 **Inline Menu System** — Button-driven UI for easy navigation
- 💾 **Persistent Sessions** — Broadcast/group selection modes persist until canceled

### Daily Static GK Bot
- 🎓 **Scheduled Quizzes** — Automated GK quizzes at defined intervals
- 🌍 **Hindi Translations** — Automatic translation to Hindi using deep-translator
- ⏰ **APScheduler Integration** — Reliable, background-running scheduler
- 🎯 **Group-Targeted Delivery** — Send quizzes to designated groups only

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Telegram Bot Tokens (create bots via [@BotFather](https://t.me/BotFather))
- pip dependencies (see installation)

### Installation

```bash
# Clone the repository
git clone https://github.com/kartikeyan-sudo/dedseg_telegram_bot.git
cd dedseg_telegram_bot

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. **DedSegBot/config.py** — Main bot settings
   ```python
   BOT_TOKEN = "your_main_bot_token_here"
   ADMIN_ID = your_admin_user_id_here
   GROUPS = [
       {"id": "-1001234567890", "name": "Group Name"},
       # Add all target groups
   ]
   ```

2. **DedSegBot/quiz_config.py** — GK bot settings
   ```python
   BOT_TOKEN = "your_gk_bot_token_here"
   TARGET_CHAT_ID = -1001234567890  # Target group for quizzes
   ```

### Running the Bots

**Terminal 1: Main Bot**
```bash
cd DedSegBot
python main.py
```

**Terminal 2: GK Bot (Scheduler)**
```bash
cd DedSegBot
python static_bot.py
```

---

## 📁 Project Structure

```
dedseg_telegram_bot/
├── DedSegBot/
│   ├── main.py              # Main bot command handler & menu system
│   ├── static_bot.py        # GK bot with APScheduler
│   ├── config.py            # Main bot & group configuration
│   ├── quiz_config.py       # GK bot configuration
│   ├── broadcast.py         # Broadcast message delivery
│   ├── quiz.py              # Quiz content & logic
│   ├── motivation.py        # Motivational quotes
│   ├── facts.py             # GK facts database
│   ├── scheduler.py         # APScheduler setup
│   └── update_offset.txt    # Polling offset cache
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

---

## 🎮 Bot Commands & Features

### Main Bot (`/start`)
- **Test Bot** — Ping the bot to verify it's online
- **Broadcast All** — Enter persistent broadcast mode for all groups
- **Broadcast Group** — Select a specific group and broadcast to it
- **Message User** — Send direct messages to users by ID or username
- **Cancel** — Exit current mode and return to menu

### Slash Commands
- `/menu` — Show the inline menu
- `/test` — Verify bot is working
- `/help` — Display help information
- `/broadcast <message>` — Quick broadcast to all groups
- `/cancel` — Cancel the current action
- `/debug` — Show your user ID and admin ID

---

## 🔒 Security Features

✅ **Admin-Only Access** — Only configured admin can use the main bot  
✅ **Private Message Forwarding** — Non-admin messages are silently forwarded to admin  
✅ **Group Deduplication** — Prevents duplicate broadcasts to the same group  
✅ **Token Isolation** — Separate tokens for main bot and GK bot  
✅ **Update Offset Caching** — Resilient polling with offset persistence  

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `requests` | HTTP calls to Telegram Bot API |
| `apscheduler` | Background task scheduling |
| `deep-translator` | Hindi & other language translations |

Install all:
```bash
pip install requests apscheduler deep-translator
```

---

## 🛠️ Development & Debugging

### Enable Debug Logging
In `DedSegBot/main.py`, the `/debug` command shows:
- Your Telegram User ID
- Configured Admin ID

### Test Broadcasts
Use the inline menu to test broadcasts to all or specific groups before production use.

### Check Bot Polling
Monitor terminal output for "Received update:" messages showing incoming Telegram updates.

---

## 🌐 Deployment

For production deployment on services like **Render**, **Railway**, or **Heroku**:

1. Set environment variables for `BOT_TOKEN`, `ADMIN_ID`, etc.
2. Run `python DedSegBot/main.py` and `python DedSegBot/static_bot.py` as background workers
3. Ensure both bot processes run continuously (use process managers like `pm2` or systemd)

---

## 📝 License

This project is open-source and available under the MIT License.

---

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

---

## 📧 Support

For issues, questions, or feature requests, please open an GitHub Issue or contact the maintainer.

---

## 🎉 Acknowledgments

Built with ❤️ for the **DedSeg** community. Special thanks to the Telegram Bot API and the open-source Python community.

---

**Happy Bot Building! 🚀**
