# Biznes Sherik — Jeke AI Biznes Járdemshi (Personal Business AI Assistant)

> Telegram bot for small business owners and course students in Karakalpakstan / Uzbekistan.  
> Built with **Python 3.12**, **aiogram 3**, **google-genai SDK (Gemini API)**, **aiosqlite**, and **APScheduler**.

---

## 🌟 Tiykarǵı Múmkinshilikler (Key Features)

1. **Step-by-Step Onboarding (`/start`)**:
   - Interactive Finite State Machine (FSM) collects student profile one question at a time:
     - Name, Business Type, City/Region, Products & Prices, Target Customer, Sales Channels, Monthly Goal, Preferred Language (`kaa`/`uz`/`ru`).
   - Saved in SQLite `profiles` table.
   - `/profile` displays formatted profile; `/edit` allows field-by-field updates or restarting.

2. **Full Business Memory & Context Injection**:
   - Every Gemini call interpolates `prompts/system.md` with:
     - The user's detailed business profile (`<profile>...</profile>`)
     - Current operational mode (`<mode>...</mode>`)
     - Chronological memory of the last 20 messages from `messages` table.

3. **Voice Message Understanding**:
   - Accepts `.ogg` voice notes, converts them directly into Gemini audio parts.
   - If the user dictates to-do items, Gemini triggers the `add_task(title, due_datetime)` function call and adds them to the database.

4. **Visual Photo Analysis**:
   - Supports receipts, handwritten checks, price lists (transcribed into tables).
   - Analyzes competitor posts (strengths, opportunities to copy, improvements).
   - Critiques own product photos with 3 practical tips to increase conversions.

5. **Task Management & Persistent Reminders**:
   - `tasks` table storing task title, status, and due datetime.
   - `/tasks` lists open tasks with inline buttons: `[✅ Done]` / `[⏰ Tomorrow]` / `[🗑 Delete]`.
   - Reminders fire at `due_datetime` via APScheduler.
   - **Persistent across restarts**: active reminders are automatically restored on bot startup from SQLite.

6. **Automated Daily Brief (08:00 Tashkent Time)**:
   - Delivers today's pending tasks.
   - Generates 1 fresh content idea tailored to the user's business + 1 actionable business tip for today.

7. **Automated Weekly Report (Sunday 20:00 Tashkent Time)**:
   - Summarizes completed vs. open tasks from the past 7 days.
   - Provides partner-level evaluation and 3 focus recommendations for next week based on monthly goals.

8. **Specialized Operational Modes**:
   - `/general` — General business partner and day planner.
   - `/content` — Writes Instagram posts, Stories, and 2-second hook Reels scripts (2 variants).
   - `/reply` — Drafts high-converting replies to customer inquiries (handles objections, closing question).
   - `/calc` — Financial calculations: unit cost, price, margin %, markup %, profit, and break-even units.
   - `/mentor` — Objective idea evaluation: 3 strengths, 3 risks, 7-day low-cost test plan, first 3 steps.

9. **Access Control & Whitelist**:
   - Whitelist system via `allowed_users` table.
   - Only whitelisted students and `ADMIN_ID` can use the bot.
   - Admin commands: `/add <id> [notes]`, `/remove <id>`, `/stats`, `/users`.

10. **Gemini Function Calling & Search Grounding**:
    - Built-in tools: `add_task`, `list_tasks`, `complete_task`, `calc_margin`.
    - Google Search grounding enabled in `/mentor` mode and when asking about live prices, competitors, and market trends.

11. **Production Quality & Fault Tolerance**:
    - Messages > 4000 characters are safely split along paragraphs/newlines while preserving and auto-closing HTML tags.
    - Chat actions (`typing`, `record_voice`, `upload_photo`) displayed during generation.
    - 60-second timeout with localized error messages.
    - Exponential backoff retry on HTTP 429 (rate limits) and 503 (transient API errors).
    - Daily rate limit: 50 requests/user/day (configurable).
    - Rotating file logging (`bot.log`) and console output.

---

## 🗂 Project Architecture

```
biznes_sherik_bot/
├── .env.example              # Template for environment variables
├── biznes-sherik.service     # Systemd unit file for Linux server deployment
├── requirements.txt          # Python dependencies
├── pytest.ini                # Pytest configuration
├── main.py                   # Bot startup, initialization, and polling loop
├── prompts/
│   └── system.md             # System prompt template for Gemini
├── src/
│   ├── config.py             # Configuration loader and validator
│   ├── db/
│   │   ├── database.py       # SQLite connection manager and table definitions
│   │   ├── access.py         # Whitelist and admin stats operations
│   │   ├── profiles.py       # User business profile operations & prompt formatter
│   │   ├── messages.py       # Per-user 20-message chat history
│   │   ├── tasks.py          # Tasks CRUD and weekly summaries
│   │   └── limits.py         # Daily rate limit tracker
│   ├── gemini/
│   │   ├── client.py         # google-genai SDK wrapper with retry & timeout
│   │   └── tools.py          # Function declarations and tool executor
│   ├── handlers/
│   │   ├── onboarding.py     # /start FSM, /profile, /edit
│   │   ├── admin.py          # /add, /remove, /stats, /users
│   │   ├── modes.py          # /general, /content, /reply, /calc, /mentor
│   │   ├── tasks.py          # /tasks, callbacks (done, tomorrow, delete)
│   │   ├── voice.py          # Voice note (.ogg) processor
│   │   ├── photo.py          # Photo & image analyzer
│   │   └── chat.py           # Standard conversational AI chat
│   ├── middleware/
│   │   ├── access.py         # Access control middleware
│   │   └── rate_limit.py     # Daily quota rate limit middleware
│   ├── scheduler/
│   │   ├── scheduler.py      # APScheduler AsyncIOScheduler runner & restorer
│   │   ├── reminders.py      # Task due-date notification dispatcher
│   │   ├── daily_brief.py    # 08:00 daily brief dispatcher
│   │   └── weekly_report.py  # Sunday 20:00 weekly report dispatcher
│   └── utils/
│       ├── formatting.py     # Telegram HTML escaping & safe message splitting (>4000)
│       ├── calc.py           # Margin, markup, profit, and break-even math
│       ├── i18n.py           # Multilingual UI strings (Karakalpak, Uzbek, Russian)
│       └── logger.py         # Rotating logger (bot.log + stdout)
└── tests/
    ├── test_fsm.py               # Onboarding FSM transition & DB persistence tests
    ├── test_tasks.py             # Task parsing & function calling tests
    ├── test_calc.py              # Margin & financial math tests
    ├── test_message_utils.py     # HTML escaping & safe splitting tests
    └── test_access_and_limits.py # Whitelist, admin stats & rate limit tests
```

---

## 🚀 Installation & Local Run

### 1. Prerequisites
- Python 3.12 (or Python 3.12+)
- Virtual environment tool (`venv`)
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- Gemini API Key from [Google AI Studio](https://aistudio.google.com/)

### 2. Clone and Setup Environment

```bash
# Clone or navigate to the project directory
cd biznes_sherik_bot

# Create and activate virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # On Linux/macOS
# On Windows:
# .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure `.env`

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```ini
# Bot credentials
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
GEMINI_API_KEY=AIzaSy...
ADMIN_ID=123456789

# AI Configuration
GEMINI_MODEL=gemini-2.5-flash
DAILY_RATE_LIMIT=50
DEFAULT_TIMEZONE=Asia/Tashkent
DB_PATH=biznes_sherik.db
LOG_LEVEL=INFO
REQUEST_TIMEOUT_SECONDS=60
```

### 4. Run the Bot

```bash
python main.py
```

---

## 🧪 Running Automated Tests

Run the full pytest suite:

```bash
pytest -v
```

All 20 unit and integration tests will run:
- Onboarding FSM questionnaire & state persistence
- Task due datetime parsing & function calling execution
- Margin %, markup %, profit & break-even calculations
- HTML tag balancing and message splitting > 4000 chars
- Whitelist authorization & daily rate limiting

---

## 🛠 Production Deployment (systemd on Ubuntu / Debian)

### 1. Copy project to server

```bash
sudo mkdir -p /opt/biznes_sherik_bot
sudo rsync -av --exclude='.venv' --exclude='__pycache__' ./ /opt/biznes_sherik_bot/
cd /opt/biznes_sherik_bot
```

### 2. Setup user and virtual environment

```bash
# Create dedicated system user
sudo useradd -r -s /bin/false -d /opt/biznes_sherik_bot botuser
sudo chown -R botuser:botuser /opt/biznes_sherik_bot

# Create venv and install dependencies
sudo -u botuser python3.12 -m venv /opt/biznes_sherik_bot/.venv
sudo -u botuser /opt/biznes_sherik_bot/.venv/bin/pip install -r requirements.txt
```

### 3. Configure systemd Service

Copy the service file:

```bash
sudo cp biznes-sherik.service /etc/systemd/system/
```

Adjust the `User=botuser` and `Group=botuser` in `/etc/systemd/system/biznes-sherik.service` if different.

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now biznes-sherik.service
```

### 4. Check Status and Logs

```bash
# Check service status
sudo systemctl status biznes-sherik.service

# Follow real-time application logs
sudo journalctl -u biznes-sherik.service -f
# Or inspect rotating file log
tail -f /opt/biznes_sherik_bot/bot.log
```

---

## 💡 Bot Commands Reference

| Command | Description |
|---|---|
| `/start` | Start bot, begin onboarding questionnaire or view greeting |
| `/profile` | View current business profile in formatted HTML |
| `/edit` | Update individual profile fields or restart questionnaire |
| `/tasks` | List pending tasks with `[✅ Done]`, `[⏰ Tomorrow]`, and `[🗑]` buttons |
| `/general` | Switch to general business assistant mode |
| `/content` | Switch to content creation mode (Reels, posts, ads) |
| `/reply` | Switch to customer reply assistant mode |
| `/calc` | Switch to financial calculation mode (margin, profit, break-even) |
| `/mentor` | Switch to business idea evaluator mode with Google Search grounding |
| `/add <id> [notes]` | *(Admin only)* Whitelist student Telegram ID |
| `/remove <id>` | *(Admin only)* Remove user from whitelist |
| `/stats` | *(Admin only)* View total users, tasks, profiles, and messages |
| `/users` | *(Admin only)* View list of all whitelisted students |

---

## 🤝 Persona & Language Guidelines

- **Karakalpak (kaa)**: Written in Latin script with correct special letters (`á, ó, ú, ı, ǵ, ń, sh, ch`).
- **Uzbek (uz)**: Modern Uzbek Latin orthography.
- **Russian (ru)**: Clear, polite business Russian.
- **Tone**: A smart, direct, experienced business co-founder (`siz`).
- **Rule of Action**: Every substantive advice ends with **one concrete next step** ("Búgin isleń: ...").
