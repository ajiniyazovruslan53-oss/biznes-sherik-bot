"""
Task management commands and callback query handlers:
/tasks listing, ✅ Done, ⏰ Tomorrow, 🗑 Delete.
"""

from datetime import datetime, timedelta, time
import zoneinfo
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from src.db.tasks import get_tasks, complete_task, reschedule_task, delete_task, get_task_by_id
from src.db.profiles import get_profile
from src.scheduler.scheduler import bot_scheduler
from src.utils.i18n import get_text
from src.utils.logger import logger
from src.config import config

router = Router(name="tasks_router")


def make_task_inline_keyboard(task_id: int, lang: str = "kaa") -> InlineKeyboardMarkup:
    """Creates [✅ Done] [⏰ Tomorrow] [🗑 Delete] inline buttons."""
    if lang == "ru":
        btn_done = "✅ Выполнено"
        btn_tomorrow = "⏰ На завтра"
        btn_delete = "🗑"
    elif lang == "uz":
        btn_done = "✅ Bajarildi"
        btn_tomorrow = "⏰ Ertaga"
        btn_delete = "🗑"
    else:
        btn_done = "✅ Bútti"
        btn_tomorrow = "⏰ Erteńge"
        btn_delete = "🗑"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=btn_done, callback_data=f"task_done:{task_id}"),
                InlineKeyboardButton(text=btn_tomorrow, callback_data=f"task_tomorrow:{task_id}"),
                InlineKeyboardButton(text=btn_delete, callback_data=f"task_delete:{task_id}"),
            ]
        ]
    )


@router.message(Command("tasks"))
async def handle_list_tasks(message: Message):
    """Displays active open tasks with action buttons."""
    user_id = message.from_user.id
    profile = await get_profile(user_id)
    lang = profile.get("preferred_language", "kaa") if profile else "kaa"

    tasks = await get_tasks(user_id=user_id, status="pending")
    if not tasks:
        await message.answer(get_text("tasks_empty", lang=lang))
        return

    header = get_text("tasks_header", lang=lang)
    await message.answer(header, parse_mode="HTML")

    for task in tasks:
        due_info = f" (⏰ {task['due_datetime']})" if task.get("due_datetime") else ""
        task_text = f"📌 <b>#{task['id']}</b>: {task['title']}{due_info}"
        await message.answer(
            task_text,
            reply_markup=make_task_inline_keyboard(task["id"], lang=lang),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("task_done:"))
async def handle_callback_task_done(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    profile = await get_profile(user_id)
    lang = profile.get("preferred_language", "kaa") if profile else "kaa"

    success = await complete_task(task_id=task_id, user_id=user_id)
    if success:
        bot_scheduler.cancel_reminder(task_id)
        msg = {
            "ru": f"✅ Задача #{task_id} выполнена!",
            "uz": f"✅ #{task_id} vazifasi bajarildi!",
            "kaa": f"✅ #{task_id} tapsırma orınlandı!"
        }.get(lang, f"✅ #{task_id} tapsırma orınlandı!")

        await callback.answer(msg)
        await callback.message.edit_text(f"<s>{callback.message.text}</s>\n\n{msg}", parse_mode="HTML")
    else:
        await callback.answer("Tapsırma tabılmadı yamasa óshirilgen.", show_alert=True)


@router.callback_query(F.data.startswith("task_tomorrow:"))
async def handle_callback_task_tomorrow(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    profile = await get_profile(user_id)
    lang = profile.get("preferred_language", "kaa") if profile else "kaa"
    tz_name = profile.get("timezone", config.DEFAULT_TIMEZONE) if profile else config.DEFAULT_TIMEZONE

    try:
        tz = zoneinfo.ZoneInfo(tz_name)
    except Exception:
        tz = zoneinfo.ZoneInfo("Asia/Tashkent")

    # Set tomorrow at 09:00
    tomorrow = datetime.now(tz).date() + timedelta(days=1)
    tomorrow_dt = datetime.combine(tomorrow, time(9, 0, 0), tzinfo=tz)
    tomorrow_str = tomorrow_dt.strftime("%Y-%m-%d %H:%M:%S")

    success = await reschedule_task(task_id=task_id, user_id=user_id, new_due_datetime=tomorrow_str)
    if success:
        task = await get_task_by_id(task_id, user_id)
        title = task["title"] if task else "Tapsırma"
        bot_scheduler.schedule_reminder(task_id, user_id, title, tomorrow_dt)

        msg = {
            "ru": f"⏰ Задача #{task_id} перенесена на завтра 09:00!",
            "uz": f"⏰ #{task_id} vazifa ertaga 09:00 ga qoldirildi!",
            "kaa": f"⏰ #{task_id} tapsırma erteń 09:00 ge qaldırıldı!"
        }.get(lang, f"⏰ #{task_id} tapsırma erteńge qaldırıldı!")

        await callback.answer(msg)
        await callback.message.edit_text(
            f"📌 <b>#{task_id}</b>: {title} (⏰ {tomorrow_str})\n\n{msg}",
            reply_markup=make_task_inline_keyboard(task_id, lang=lang),
            parse_mode="HTML"
        )
    else:
        await callback.answer("Qátelik júz berdi.", show_alert=True)


@router.callback_query(F.data.startswith("task_delete:"))
async def handle_callback_task_delete(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    profile = await get_profile(user_id)
    lang = profile.get("preferred_language", "kaa") if profile else "kaa"

    success = await delete_task(task_id=task_id, user_id=user_id)
    if success:
        bot_scheduler.cancel_reminder(task_id)
        msg = {
            "ru": f"🗑 Задача #{task_id} удалена.",
            "uz": f"🗑 #{task_id} vazifasi o'chirildi.",
            "kaa": f"🗑 #{task_id} tapsırma óshirildi."
        }.get(lang, f"🗑 #{task_id} tapsırma óshirildi.")

        await callback.answer(msg)
        await callback.message.edit_text(f"<s>{callback.message.text}</s>\n\n{msg}", parse_mode="HTML")
    else:
        await callback.answer("Tapsırma tabılmadı.", show_alert=True)
