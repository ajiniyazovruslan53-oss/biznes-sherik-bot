"""
General text chat handler:
Handles free-form business questions, mode-specific inquiries, calculations,
and task creations via natural language text.
"""

from aiogram import Router, F, Bot
from aiogram.types import Message

from src.db.profiles import get_profile
from src.db.messages import get_recent_messages, save_message
from src.gemini.client import gemini_service
from src.scheduler.scheduler import bot_scheduler
from src.scheduler.reminders import parse_datetime
from src.utils.formatting import markdown_to_telegram_html, split_message
from src.utils.logger import logger
from src.config import config

router = Router(name="chat_router")


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text_chat(message: Message, bot: Bot):
    """Processes user text messages and generates AI response."""
    user_id = message.from_user.id
    profile = await get_profile(user_id)
    lang = profile.get("preferred_language", "kaa") if profile else "kaa"
    mode = profile.get("current_mode", "general") if profile else "general"

    # Send typing action
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # Callback to schedule reminder if Gemini adds a task
    async def scheduler_callback(task_id: int, u_id: int, title: str, due_str: str):
        due_dt = parse_datetime(due_str, profile.get("timezone", config.DEFAULT_TIMEZONE) if profile else config.DEFAULT_TIMEZONE)
        if due_dt:
            bot_scheduler.schedule_reminder(task_id, u_id, title, due_dt)

    try:
        # Load conversation memory (last 20 messages)
        history = await get_recent_messages(user_id=user_id, limit=20)

        response_text = await gemini_service.generate_response(
            user_id=user_id,
            prompt_parts=message.text,
            profile=profile,
            mode=mode,
            history=history,
            scheduler_callback=scheduler_callback
        )

        # Save to database memory
        await save_message(user_id, "user", message.text)
        await save_message(user_id, "model", response_text)

        # Format and split HTML response safely
        html_text = markdown_to_telegram_html(response_text)
        chunks = split_message(html_text)
        for chunk in chunks:
            await message.answer(chunk, parse_mode="HTML")

    except TimeoutError:
        err_msg = {
            "ru": "⚠️ Время ожидания ответа истекло (60 сек). Пожалуйста, повторите запрос чуть позже.",
            "uz": "⚠️ Javob kutish vaqti tugadi (60 sek). Iltimos, birozdan so'ng qayta urinib ko'ring.",
            "kaa": "⚠️ Keshirersiz, serverden juwap kútiw waqtı tawsıldı (60 sek). Qaytadan urınıp kóriń."
        }.get(lang, "⚠️ Keshirersiz, waqıt tawsıldı.")
        await message.answer(err_msg)

    except Exception as e:
        logger.error(f"Error handling chat message for user {user_id}: {e}", exc_info=True)
        await message.answer("⚠️ Sorawıńızdı qayta islewde qátelik júz berdi. Qaytadan urınıp kóriń.")
