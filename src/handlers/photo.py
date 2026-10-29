"""
Photo handler:
Downloads photos (receipts, price lists, competitor posts, product photos)
and sends them to Gemini as image parts for visual business analysis.
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

router = Router(name="photo_router")


@router.message(F.photo)
async def handle_photo_message(message: Message, bot: Bot):
    """Processes photos sent by user."""
    user_id = message.from_user.id
    profile = await get_profile(user_id)
    lang = profile.get("preferred_language", "kaa") if profile else "kaa"
    mode = profile.get("current_mode", "general") if profile else "general"

    # Show typing / uploading action
    await bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")

    # Download largest photo
    photo_size = message.photo[-1]
    file_io = io.BytesIO()
    try:
        await bot.download(photo_size, destination=file_io)
        photo_bytes = file_io.getvalue()
    except Exception as e:
        logger.error(f"Failed to download photo for user {user_id}: {e}", exc_info=True)
        await message.answer("⚠️ Súwretti júklep alıwda qátelik boldı. Qaytadan jiberip kóriń.")
        return

    # Prepare caption or default prompt
    caption = message.caption or ""
    if not caption.strip():
        caption_instruction = (
            "Usı súwretti kózden ótkeriń:\n"
            "- Eger shek yamasa baha dizimi (prays-list) bolsa: tovarlar hám bahalardı keste (tablica) qılıp shıǵarıń.\n"
            "- Eger konkurenttiń posti yamasa reklaması bolsa: ne jaqsı islengen, neni ózimizge alsa boladı, neni bunnan da jaqsıraq qılıw kerek.\n"
            "- Eger óz ónimińizdiń fotosúwreti bolsa: onı satıwshı qılıw ushın anıq 3 jaqsılaw keńesin beriń."
        )
    else:
        caption_instruction = f"Paydalanıwshı túsindirmesi: {caption}"

    # Callback to schedule reminder if Gemini adds a task
    async def scheduler_callback(task_id: int, u_id: int, title: str, due_str: str):
        due_dt = parse_datetime(due_str, profile.get("timezone", config.DEFAULT_TIMEZONE) if profile else config.DEFAULT_TIMEZONE)
        if due_dt:
            bot_scheduler.schedule_reminder(task_id, u_id, title, due_dt)

    try:
        history = await get_recent_messages(user_id=user_id, limit=20)
        image_part = types.Part.from_bytes(data=photo_bytes, mime_type="image/jpeg")
        prompt_parts = [caption_instruction, image_part]

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
        saved_caption = f"[Foto / Изображение]: {caption}" if caption else "[Foto / Изображение]"
        await save_message(user_id, "user", saved_caption)
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
        logger.error(f"Error handling photo message for user {user_id}: {e}", exc_info=True)
        await message.answer("⚠️ Súwretti qayta islewde qátelik júz berdi.")
