"""
Vercel Serverless Webhook Handler for Biznes Sherik Bot.
Handles incoming Telegram webhook updates via serverless HTTP POST.
"""

import json
import asyncio
import os
from http.server import BaseHTTPRequestHandler
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Adjust DB_PATH for Vercel serverless environment (/tmp)
if os.getenv("VERCEL"):
    os.environ["DB_PATH"] = "/tmp/biznes_sherik.db"

from src.config import config
from src.db.database import init_db
from src.handlers import register_all_handlers
from src.middleware import AccessMiddleware, RateLimitMiddleware

# Initialize Bot & Dispatcher once per lambda container
bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Middlewares
dp.message.middleware(AccessMiddleware())
dp.callback_query.middleware(AccessMiddleware())
dp.message.middleware(RateLimitMiddleware())

# Handlers
register_all_handlers(dp)

# Flag for DB initialization in container
_db_initialized = False


async def process_telegram_update(data: dict):
    """Feeds Telegram update to aiogram dispatcher."""
    global _db_initialized
    if not _db_initialized:
        await init_db()
        _db_initialized = True

    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function entry handler."""

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        response = {
            "status": "online",
            "bot": "Biznes Sherik",
            "message": "Webhook handler is running on Vercel."
        }
        self.wfile.write(json.dumps(response).encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            update_dict = json.loads(post_data.decode("utf-8"))
            asyncio.run(process_telegram_update(update_dict))
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
