"""
Daily brief generator and dispatcher at 08:00 (user's timezone).
Sends:
- Today's pending tasks
- 1 fresh content idea tailored to profile
- 1 practical business tip
"""

from typing import Optional
from datetime import datetime
import zoneinfo
from aiogram import Bot

from src.db.profiles import get_all_profiles
from src.db.tasks import get_tasks
from src.gemini.client import gemini_service
from src.utils.logger import logger
from src.utils.formatting import markdown_to_telegram_html, split_message


async def send_daily_briefs(bot: Bot) -> None:
    """Iterates through all registered business profiles and delivers the morning daily brief."""
    logger.info("Executing scheduled Daily Brief job...")
    profiles = await get_all_profiles()

    for profile in profiles:
        user_id = profile["user_id"]
        lang = profile.get("preferred_language", "kaa")
        tz_name = profile.get("timezone", "Asia/Tashkent")

        try:
            # 1. Fetch pending tasks
            pending_tasks = await get_tasks(user_id=user_id, status="pending")

            tasks_text = ""
            if pending_tasks:
                items = [f"• {t['title']}" + (f" (⏰ {t['due_datetime']})" if t['due_datetime'] else "") for t in pending_tasks[:5]]
                tasks_text = "\n".join(items)
            else:
                if lang == "ru":
                    tasks_text = "• На сегодня нет запланированных задач."
                elif lang == "uz":
                    tasks_text = "• Bugun uchun rejalashtirilgan vazifalar yo'q."
                else:
                    tasks_text = "• Búginge rejelestirilgen tapsırmalar joq."

            # 2. Prompt Gemini for 1 content idea + 1 business tip
            prompt = (
                f"Búgin tańǵı xabar (Daily brief) waqtı. Paydalanıwshı profiline qarap:\n"
                f"1) Búgingi kún ushın 1 anıq, qızıqlı kontent ideyasın beriń (Reels yamasa post ushın anıq tema hám qısqa tema).\n"
                f"2) Biznesti rawajlandırıw, satıwdı asırıw boyınsha 1 ámeliy qısqa keńes (búgin qılıwǵa bolatuǵın ámeliy qádem).\n"
                f"Juwap stili: qısqa, júdá anıq, suwı joq, paydalanıwshı tilinde ({lang})."
            )

            response_raw = await gemini_service.generate_response(
                user_id=user_id,
                prompt_parts=prompt,
                profile=profile,
                mode="general",
                history=None
            )

            # 3. Assemble full brief message
            if lang == "ru":
                header = "🌅 <b>Доброе утро! Ваш утренний дайджест:</b>\n\n"
                tasks_section = f"📋 <b>Ваши текущие задачи:</b>\n{tasks_text}\n\n"
            elif lang == "uz":
                header = "🌅 <b>Xayrli tong! Sizning kunlik dayjestingiz:</b>\n\n"
                tasks_section = f"📋 <b>Bugungi vazifalaringiz:</b>\n{tasks_text}\n\n"
            else:
                header = "🌅 <b>Xayrli tań! Búgingi kúnińizge reje:</b>\n\n"
                tasks_section = f"📋 <b>Búgingi tapsırmalarıńız:</b>\n{tasks_text}\n\n"

            gemini_html = markdown_to_telegram_html(response_raw)
            full_text = header + tasks_section + gemini_html

            chunks = split_message(full_text)
            for chunk in chunks:
                await bot.send_message(chat_id=user_id, text=chunk, parse_mode="HTML")

            logger.info(f"Daily brief sent to user {user_id}")

        except Exception as e:
            logger.error(f"Failed to generate/send daily brief for user {user_id}: {e}", exc_info=True)
