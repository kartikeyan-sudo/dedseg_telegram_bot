# 🎯 DedSeg Telegram Bot Ecosystem

A powerful Telegram bot ecosystem for the **DedSeg** community — automated quizzes, admin broadcasts, motivational content, and daily GK facts. Features a **Livegram-style** public-facing chat experience and a secure admin-only control panel.

---

## 📋 Overview

| Bot | Purpose |
|-----|---------|
| **DedSeg Main Bot** | Admin control center — broadcasts, group targeting, user messaging, stats |
| **Daily Static GK Bot** | Scheduled quizzes, GK facts, motivational quotes with Hindi translation |

Both bots use **Livegram-style UX** for regular users and a secure **admin-only panel** for management.

---

## ✨ Features

### 🎛 DedSeg Main Bot (Admin Panel)
- 🔐 **Admin-only commands** — scoped via Telegram's `setMyCommands` API; non-admins see NO commands
- 📩 **Livegram mode** — regular users get a friendly welcome and can send messages to admin
- 🔁 **Two-way messaging** — admin can `/reply <user_id> <message>` directly from the bot
- 📢 **Smart broadcasts** — broadcast to all groups or target a specific group
- 👤 **Direct user messaging** — send personalized messages to any user by ID
- 📊 **Stats panel** — view uptime, group count, last broadcast time
- 📋 **List groups** — see all configured groups with IDs inline
- 💾 **Persistent sessions** — broadcast modes persist until cancelled

### 📚 Daily Static GK Bot
- 🎓 **Scheduled quizzes** — auto-runs at 8 AM, 1 PM (facts), and 9 PM (motivation)
- 🌍 **Hindi translations** — all questions sent in English + Hindi
- 🔄 **API retry logic** — handles OpenTDB rate limits gracefully
- ⚠️ **Error-resilient** — fallback messages if any external API is down
- 👤 **Livegram mode** — users get a welcome message; text is forwarded to admin

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Two Telegram Bot tokens (create via [@BotFather](https://t.me/BotFather))

### Installation

```bash
git clone https://github.com/kartikeyan-sudo/dedseg_telegram_bot.git
cd dedseg_telegram_bot

pip install -r DedSegBot/requirements.txt
```

### Configuration

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Fill in your `.env`:
   ```env
   BOT_TOKEN=your_main_bot_token
   ADMIN_ID=your_telegram_user_id
   QUIZ_BOT_TOKEN=your_quiz_bot_token
   QUIZ_CHAT_ID=-1001234567890
   ```

3. *(Optional)* Update group IDs in `DedSegBot/config.py` if needed.

### Running

**Both bots together (recommended):**
```bash
python run.py
```

**Individual bots:**
```bash
# Terminal 1 — Main Bot
cd DedSegBot && python main.py

# Terminal 2 — GK Bot
cd DedSegBot && python static_bot.py
```

---

## 📁 Project Structure

```
dedseg_telegram_bot/
├── app.py                   # FastAPI backend for Render deployment
├── run.py                   # Unified entry point (both bots in threads)
├── Procfile                 # Heroku/Railway deployment
├── render.yaml              # Render deployment config (Web Service)
├── .env.example             # Environment variable template
├── .gitattributes           # LF line ending enforcement
├── DedSegBot/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # Main admin control bot
│   ├── static_bot.py        # GK quiz bot with scheduler
│   ├── config.py            # Main bot config (env-aware)
│   ├── quiz_config.py       # GK bot config (env-aware)
│   ├── broadcast.py         # Broadcast delivery module
│   ├── quiz.py              # Quiz content with API retry
│   ├── motivation.py        # Motivational quotes
│   ├── facts.py             # GK daily facts
│   ├── scheduler.py         # APScheduler setup
│   └── requirements.txt     # Python dependencies
└── README.md
```

---

## 🎮 Bot Commands

### Admin (Main Bot) — `/start`
| Command | Description |
|---------|-------------|
| `/menu` | Show admin panel |
| `/broadcast <msg>` | Quick broadcast to all groups |
| `/reply <user_id> <msg>` | Reply to a forwarded user message |
| `/stats` | Show uptime, group count, last broadcast |
| `/test` | Ping the bot |
| `/cancel` | Cancel current action |

### Admin (GK Bot)
| Command | Description |
|---------|-------------|
| `/quiz` | Trigger quiz manually |
| `/menu` | Show GK bot menu |

### Users (both bots)
- `/start` — Friendly welcome message
- Text messages — Forwarded to admin silently

---

## 🔒 Security

| Feature | Detail |
|---------|--------|
| Scoped commands | Admin commands invisible to non-admin users |
| Silent drops | Non-admin commands produce no error or response |
| Livegram forwarding | User messages forwarded to admin privately |
| Two-way replies | Admin can reply to users via `/reply` |
| Env-based secrets | Tokens never hardcoded in production |

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `requests` | Telegram Bot API calls |
| `apscheduler` | Background task scheduling |
| `deep-translator` | Hindi translations |
| `python-dotenv` | `.env` secret management |

---

## 🌐 Deploying to Render

### Step-by-step guide

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Go to [render.com](https://render.com)** and sign in with GitHub.

3. **Create a new service:**
   - Click **New → Web Service**
   - Connect your `dedseg_telegram_bot` repository
   - Render will auto-detect `render.yaml`

4. **Set environment variables** in the Render dashboard:
   | Key | Value |
   |-----|-------|
   | `BOT_TOKEN` | Your main bot token |
   | `ADMIN_ID` | Your Telegram user ID |
   | `QUIZ_BOT_TOKEN` | Your GK bot token |
   | `QUIZ_CHAT_ID` | Target group ID for quizzes |
   | `GROUP_1_ID` … `GROUP_5_ID` | *(optional)* Override group IDs |

5. **Click Deploy** — Render will install dependencies and run `python run.py`.

6. **Verify** — Open Telegram, message your bot from the admin account. You should see the admin panel.

> [!TIP]
> Render's free tier puts services to sleep after inactivity. For a bot, use the **Starter** plan ($7/mo) or Railway which keeps workers always-on.

---

## 🛠️ Local Development

```bash
# Run with hot-reload friendly setup
cd DedSegBot
python -c "from config import ADMIN_ID; print('Admin ID:', ADMIN_ID)"  # verify config

python run.py  # from project root
```

Monitor terminal for `[main_bot]` and `[gk_bot]` prefixed logs.

---

## 📝 License

MIT License — open source, free to use and modify.

---

**Built with ❤️ for the DedSeg community. Happy Bot Building! 🚀**