"""
Voice message handler:
Downloads voice .ogg message, converts to audio Part, and forwards to Gemini.
Handles dictated tasks via function calling (add_task) and business queries.
"""

import io
from aiogram import Router, F, Bot
from aiogram.types import Message
from google.genai import types

from src.db.profiles import get_profile
from src.db.messages import get_recent_messages, save_message
from src.gemini.client import gemini_service
from src.scheduler.scheduler import bot_scheduler
from src.scheduler.reminders import parse_datetime
from src.utils.formatting import markdown_to_telegram_html, split_message
from src.utils.logger import logger
from src.config import config

router = Router(name="voice_router")


@router.message(F.voice)
async def handle_voice_message(message: Message, bot: Bot):
    """Processes audio voice message sent by user."""
    user_id = message.from_user.id
    profile = await get_profile(user_id)
    lang = profile.get("preferred_language", "kaa") if profile else "kaa"
    mode = profile.get("current_mode", "general") if profile else "general"

    # Show typing / recording action
    await bot.send_chat_action(chat_id=message.chat.id, action="record_voice")

    # Download voice file to memory
    file_io = io.BytesIO()
    try:
        await bot.download(message.voice, destination=file_io)
        voice_bytes = file_io.getvalue()
    except Exception as e:
        logger.error(f"Failed to download voice file for user {user_id}: {e}", exc_info=True)
        await message.answer("⚠️ Dawıslı xabardı júklep alıwda qátelik boldı. Qaytadan jiberip kóriń.")
        return

    # Callback to schedule reminder if Gemini adds a task
    async def scheduler_callback(task_id: int, u_id: int, title: str, due_str: str):
        due_dt = parse_datetime(due_str, profile.get("timezone", config.DEFAULT_TIMEZONE) if profile else config.DEFAULT_TIMEZONE)
        if due_dt:
            bot_scheduler.schedule_reminder(task_id, u_id, title, due_dt)

    try:
        # Load conversation memory (last 20 messages)
        history = await get_recent_messages(user_id=user_id, limit=20)

        # Create audio part
        audio_part = types.Part.from_bytes(data=voice_bytes, mime_type="audio/ogg")
        prompt_parts = [
            "Tómendegi dawıslı xabardı tıńlań hám paydalanıwshıǵa Biznes Sherik sıpatında juwap beriń. "
            "Eger tapsırma yamasa islengen jumıs tapsırılsa, add_task quralın shaqırıń.",
            audio_part
        ]

        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        response_text = await gemini_service.generate_response(
            user_id=user_id,
            prompt_parts=prompt_parts,
            profile=profile,
            mode=mode,
            history=history,
            scheduler_callback=scheduler_callback
        )

        # Save to memory
        await save_message(user_id, "user", "[Dawıslı xabar / Голосовое сообщение]")
        await save_message(user_id, "model", response_text)

        # Format and send response
        html_text = markdown_to_telegram_html(response_text)
        chunks = split_message(html_text)
        for chunk in chunks:
            await message.answer(chunk, parse_mode="HTML")

    except TimeoutError:
        err_msg = {
            "ru": "⚠️ Время ожидания ответа истекло (60 сек). Пожалуйста, повторите запрос.",
            "uz": "⚠️ Javob kutish vaqti tugadi (60 sek). Iltimos, qayta urinib ko'ring.",
            "kaa": "⚠️ Keshirersiz, serverden juwap kútiw waqtı tawsıldı (60 sek). Qaytadan urınıp kóriń."
        }.get(lang, "⚠️ Keshirersiz, waqıt tawsıldı.")
        await message.answer(err_msg)

    except Exception as e:
        logger.error(f"Error handling voice message for user {user_id}: {e}", exc_info=True)
        await message.answer("⚠️ Dawıslı xabardı qayta islewde qátelik júz berdi.")
