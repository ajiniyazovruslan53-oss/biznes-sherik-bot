"""
Task reminder parsing and execution via APScheduler.
"""

from datetime import datetime, time, timedelta
import zoneinfo
import re
from typing import Optional
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.db.tasks import get_task_by_id
from src.db.profiles import get_profile
from src.utils.logger import logger
from src.config import config


def parse_datetime(dt_str: str, tz_name: str = config.DEFAULT_TIMEZONE) -> Optional[datetime]:
    """
    Parses various date/time formats into timezone-aware datetime.
    Supports:
    - YYYY-MM-DD HH:MM:SS
    - YYYY-MM-DDTHH:MM:SS
    - YYYY-MM-DD HH:MM
    - YYYY-MM-DD (defaults to 09:00 morning)
    """
    if not dt_str:
        return None

    dt_str = dt_str.strip()
    try:
        tz = zoneinfo.ZoneInfo(tz_name)
    except Exception:
        tz = zoneinfo.ZoneInfo("Asia/Tashkent")

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y %H:%M:%S",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(dt_str, fmt)
            return dt.replace(tzinfo=tz)
        except ValueError:
            continue

    # Date only format YYYY-MM-DD or DD.MM.YYYY
    date_formats = ["%Y-%m-%d", "%d.%m.%Y"]
    for dfmt in date_formats:
        try:
            d = datetime.strptime(dt_str, dfmt).date()
            dt = datetime.combine(d, time(9, 0, 0))  # 9 AM default
            return dt.replace(tzinfo=tz)
        except ValueError:
            continue

    # Attempt regex ISO 8601 extraction
    match = re.search(r"(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})", dt_str)
    if match:
        try:
            date_part, time_part = match.group(1), match.group(2)
            dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
            return dt.replace(tzinfo=tz)
        except ValueError:
            pass

    return None


async def send_task_reminder(bot: Bot, task_id: int, user_id: int, title: str) -> None:
    """Dispatches a task reminder message to user if task is still pending."""
    try:
        task = await get_task_by_id(task_id, user_id)
        if not task or task["status"] == "completed":
            logger.info(f"Reminder for task {task_id} skipped: task completed or not found.")
            return

        profile = await get_profile(user_id)
        lang = profile.get("preferred_language", "kaa") if profile else "kaa"

        if lang == "ru":
            text = f"⏰ <b>Напоминание о задаче:</b>\n\n📌 <b>{task['title']}</b>\n\nНе забудьте выполнить сегодня!"
            btn_done = "✅ Выполнено"
            btn_tomorrow = "⏰ На завтра"
        elif lang == "uz":
            text = f"⏰ <b>Vazifa eslatmasi:</b>\n\n📌 <b>{task['title']}</b>\n\nBugun bajarishni unutmang!"
            btn_done = "✅ Bajarildi"
            btn_tomorrow = "⏰ Ertaga"
        else:  # Karakalpak
            text = f"⏰ <b>Tapsırma esletpesi:</b>\n\n📌 <b>{task['title']}</b>\n\nBúgin orınlawdı umıtpań!"
            btn_done = "✅ Bútti"
            btn_tomorrow = "⏰ Erteńge"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text=btn_done, callback_data=f"task_done:{task_id}"),
                    InlineKeyboardButton(text=btn_tomorrow, callback_data=f"task_tomorrow:{task_id}")
                ]
            ]
        )

        await bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        logger.info(f"Reminder sent successfully to user {user_id} for task {task_id}")

    except Exception as e:
        logger.error(f"Failed to send task reminder for task {task_id} to user {user_id}: {e}", exc_info=True)
