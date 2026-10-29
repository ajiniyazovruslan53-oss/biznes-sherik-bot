"""
Mode switching commands handler:
/general, /content, /reply, /calc, /mentor
Updates current_mode in profiles table and sends localized confirmation.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.db.profiles import get_profile, update_profile_field
from src.utils.i18n import get_text
from src.utils.logger import logger

router = Router(name="modes_router")


async def switch_mode(message: Message, new_mode: str) -> None:
    user_id = message.from_user.id
    profile = await get_profile(user_id)
    lang = profile.get("preferred_language", "kaa") if profile else "kaa"

    await update_profile_field(user_id, "current_mode", new_mode)
    logger.info(f"User {user_id} switched mode to '{new_mode}'")

    key_map = {
        "general": "mode_switched_general",
        "content": "mode_switched_content",
        "reply": "mode_switched_reply",
        "calc": "mode_switched_calc",
        "mentor": "mode_switched_mentor",
    }
    text = get_text(key_map.get(new_mode, "mode_switched_general"), lang=lang)
    await message.answer(text, parse_mode="HTML")


@router.message(Command("general"))
async def handle_general_mode(message: Message):
    await switch_mode(message, "general")


@router.message(Command("content"))
async def handle_content_mode(message: Message):
    await switch_mode(message, "content")


@router.message(Command("reply"))
async def handle_reply_mode(message: Message):
    await switch_mode(message, "reply")


@router.message(Command("calc"))
async def handle_calc_mode(message: Message):
    await switch_mode(message, "calc")


@router.message(Command("mentor"))
async def handle_mentor_mode(message: Message):
    await switch_mode(message, "mentor")
