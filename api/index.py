"""
Vercel Serverless Webhook Handler for Biznes Sherik Bot.
Handles incoming Telegram webhook updates via serverless HTTP POST.
"""

import json
import asyncio
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# Add project root to sys.path so 'src' can be imported anywhere on Vercel
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Adjust DB_PATH for Vercel serverless environment (/tmp)
if os.getenv("VERCEL"):
    os.environ["DB_PATH"] = "/tmp/biznes_sherik.db"

_bot = None
_dp = None
_init_error = None


def get_bot_and_dp():
    """Lazily initializes Bot and Dispatcher to gracefully catch config errors."""
    global _bot, _dp, _init_error
    if _init_error:
        raise _init_error
    if _bot is not None and _dp is not None:
        return _bot, _dp

    try:
        from src.config import config
        from src.db.database import init_db
        from src.handlers import register_all_handlers
        from src.middleware import AccessMiddleware, RateLimitMiddleware
        from aiogram import Bot, Dispatcher
        from aiogram.enums import ParseMode
        from aiogram.client.default import DefaultBotProperties

        if not config.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is not configured in Vercel Environment Variables.")

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

        _bot = bot
        _dp = dp
        return _bot, _dp
    except Exception as e:
        _init_error = e
        raise e


_db_initialized = False


async def process_telegram_update(data: dict):
    """Feeds Telegram update to aiogram dispatcher."""
    global _db_initialized
    bot, dp = get_bot_and_dp()

    if not _db_initialized:
        from src.db.database import init_db
        await init_db()
        _db_initialized = True

    from aiogram.types import Update
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function entry handler."""

    def do_GET(self):
        try:
            bot, dp = get_bot_and_dp()
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            response = {
                "status": "online",
                "bot": "Biznes Sherik",
                "message": "Webhook handler is running on Vercel."
            }
            self.wfile.write(json.dumps(response).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            response = {
                "status": "error",
                "error": str(e)
            }
            self.wfile.write(json.dumps(response).encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            update_dict = json.loads(post_data.decode("utf-8"))
            asyncio.run(process_telegram_update(update_dict))
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
