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

_dp = None
_db_initialized = False


def get_dispatcher():
    """Initializes Dispatcher once with middlewares and handlers."""
    global _dp
    if _dp is not None:
        return _dp

    from src.handlers.admin import router as admin_router
    from src.handlers.onboarding import router as onboarding_router
    from src.handlers.modes import router as modes_router
    from src.handlers.tasks import router as tasks_router
    from src.handlers.voice import router as voice_router
    from src.handlers.photo import router as photo_router
    from src.handlers.chat import router as chat_router
    from src.middleware import AccessMiddleware, RateLimitMiddleware
    from aiogram import Dispatcher

    dp = Dispatcher()

    # Middlewares
    dp.message.middleware(AccessMiddleware())
    dp.callback_query.middleware(AccessMiddleware())
    dp.message.middleware(RateLimitMiddleware())

    # Handlers (cleanly reset parent before attaching)
    routers = [
        admin_router, onboarding_router, modes_router,
        tasks_router, voice_router, photo_router, chat_router
    ]
    for r in routers:
        r._parent_router = None
        dp.include_router(r)

    _dp = dp
    return _dp


def create_bot():
    """Creates a fresh Bot instance tied to the active event loop."""
    from src.config import config
    from aiogram import Bot
    from aiogram.enums import ParseMode
    from aiogram.client.default import DefaultBotProperties

    if not config.BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not configured in Vercel Environment Variables.")

    return Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )


async def process_telegram_update(data: dict):
    """Processes incoming Telegram update inside a fresh bot session."""
    global _db_initialized
    bot = create_bot()
    dp = get_dispatcher()

    try:
        if not _db_initialized:
            from src.db.database import init_db
            await init_db()
            _db_initialized = True

        from aiogram.types import Update
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot, update)
    finally:
        await bot.session.close()


async def check_health() -> dict:
    """Performs quick healthcheck for GET request."""
    bot = create_bot()
    try:
        me = await bot.get_me()
        return {
            "status": "online",
            "bot": f"@{me.username}",
            "name": me.first_name,
            "message": "Webhook handler is running on Vercel."
        }
    finally:
        await bot.session.close()


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function entry handler."""

    def do_GET(self):
        try:
            health = asyncio.run(check_health())
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(health).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "error": str(e)}).encode("utf-8"))

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
