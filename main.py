"""
Main entry point for Biznes Sherik Telegram Bot.
"""

import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties

from src.config import config
from src.db.database import init_db
from src.handlers import register_all_handlers
from src.middleware import AccessMiddleware, RateLimitMiddleware
from src.scheduler.scheduler import bot_scheduler
from src.utils.logger import logger


async def set_bot_commands(bot: Bot) -> None:
    """Sets standard menu commands in Telegram UI."""
    commands = [
        BotCommand(command="start", description="Baslaw / Старт"),
        BotCommand(command="profile", description="Biznes profili / Профиль"),
        BotCommand(command="edit", description="Profildi ózgertiw / Редактировать"),
        BotCommand(command="tasks", description="Tapsırmalar / Задачи"),
        BotCommand(command="general", description="Tiykarǵı járdemshi / Основной"),
        BotCommand(command="content", description="Kontent rejimi / Контент"),
        BotCommand(command="reply", description="Klientke juwap / Ответ клиенту"),
        BotCommand(command="calc", description="Qarjı esap-kitabı / Расчёты"),
        BotCommand(command="mentor", description="Ideya analizi / Ментор"),
    ]
    try:
        await bot.set_my_commands(commands)
    except Exception as e:
        logger.warning(f"Failed to set bot commands: {e}")


async def main() -> None:
    # 1. Validate configuration
    try:
        config.validate(check_secrets=True)
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        print(f"\n[!] Configuration Error: {e}")
        print("Please check your .env file. See .env.example for details.\n")
        sys.exit(1)

    logger.info("Starting Biznes Sherik Bot...")

    # 2. Initialize Database
    await init_db()

    # 3. Create Bot and Dispatcher
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # 4. Setup Middlewares
    dp.message.middleware(AccessMiddleware())
    dp.callback_query.middleware(AccessMiddleware())
    dp.message.middleware(RateLimitMiddleware())

    # 5. Register Handlers
    register_all_handlers(dp)

    # 6. Setup Bot Commands
    await set_bot_commands(bot)

    # 7. Start Scheduler & Restore Reminders
    bot_scheduler.start(bot)
    await bot_scheduler.restore_task_reminders(bot)

    # 8. Start Polling
    logger.info("Bot started polling.")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        logger.info("Shutting down bot...")
        if bot_scheduler.scheduler.running:
            bot_scheduler.scheduler.shutdown()
        await bot.session.close()
        logger.info("Bot shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user.")
