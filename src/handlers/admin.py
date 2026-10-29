"""
Admin commands handler:
/add <user_id> [notes] - adds student to allowed_users
/remove <user_id> - removes student from allowed_users
/stats - displays overall usage statistics
/users - lists current allowed students
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from src.config import config
from src.db.access import add_allowed_user, remove_allowed_user, get_system_stats, list_allowed_users
from src.utils.logger import logger

router = Router(name="admin_router")


def is_admin(user_id: int) -> bool:
    return user_id == config.ADMIN_ID and config.ADMIN_ID != 0


@router.message(Command("add"))
async def handle_add_user(message: Message):
    """Admin command to whitelist a student ID."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizde administrator huqıqı joq.")
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        await message.answer("⚠️ Qollanıw: <code>/add &lt;Telegram_ID&gt; [esletpe]</code>", parse_mode="HTML")
        return

    try:
        target_id = int(parts[1])
        notes = parts[2] if len(parts) > 2 else ""
        await add_allowed_user(user_id=target_id, added_by=message.from_user.id, notes=notes)
        await message.answer(f"✅ Paydalanıwshı <code>{target_id}</code> bazaga qosıldı!", parse_mode="HTML")
        logger.info(f"Admin {message.from_user.id} added user {target_id} (notes: '{notes}')")
    except ValueError:
        await message.answer("⚠️ Telegram ID tek sanlardan ibarat bolıwı kerek.")


@router.message(Command("remove"))
async def handle_remove_user(message: Message):
    """Admin command to remove a user from allowed_users."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizde administrator huqıqı joq.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("⚠️ Qollanıw: <code>/remove &lt;Telegram_ID&gt;</code>", parse_mode="HTML")
        return

    try:
        target_id = int(parts[1])
        removed = await remove_allowed_user(target_id)
        if removed:
            await message.answer(f"✅ Paydalanıwshı <code>{target_id}</code> bazadan óshirildi.", parse_mode="HTML")
        else:
            await message.answer(f"ℹ️ Paydalanıwshı <code>{target_id}</code> bazadan tabılmadı.", parse_mode="HTML")
    except ValueError:
        await message.answer("⚠️ Telegram ID tek sanlardan ibarat bolıwı kerek.")


@router.message(Command("stats"))
async def handle_stats(message: Message):
    """Admin command to view system statistics."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizde administrator huqıqı joq.")
        return

    stats = await get_system_stats()
    text = (
        "📊 <b>Biznes Sherik — Bot Statistikası</b>\n\n"
        f"👥 Ruxsat berilgen studentler: <b>{stats['allowed_users']}</b>\n"
        f"📝 Toltırılǵan profiller: <b>{stats['profiles_completed']}</b>\n"
        f"⏳ Kútip turǵan tapsırmalar: <b>{stats['pending_tasks']}</b>\n"
        f"✅ Bajarilgen tapsırmalar: <b>{stats['completed_tasks']}</b>\n"
        f"💬 Búgingi xabarlar: <b>{stats['today_messages']}</b>\n"
        f"📚 Jámi xabarlar sanı: <b>{stats['total_messages']}</b>\n"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("users"))
async def handle_list_users(message: Message):
    """Admin command to list all allowed students."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizde administrator huqıqı joq.")
        return

    users = await list_allowed_users()
    if not users:
        await message.answer("Házirshe ruxsat berilgen paydalanıwshılar joq.")
        return

    lines = ["👥 <b>Ruxsat berilgen studentler dizimi:</b>\n"]
    for u in users:
        note_str = f" ({u['notes']})" if u.get("notes") else ""
        lines.append(f"• <code>{u['user_id']}</code>{note_str} — {u.get('created_at', '')[:10]}")

    await message.answer("\n".join(lines), parse_mode="HTML")
