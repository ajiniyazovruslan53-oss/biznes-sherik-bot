"""
Weekly report generator and dispatcher at Sunday 20:00 (user's timezone).
Sends:
- Completed tasks vs open tasks from past 7 days
- AI evaluation of weekly progress against monthly goal
- Practical focus suggestions for next week
"""

from typing import Optional
from aiogram import Bot

from src.db.profiles import get_all_profiles
from src.db.tasks import get_tasks_summary_for_period
from src.gemini.client import gemini_service
from src.utils.logger import logger
from src.utils.formatting import markdown_to_telegram_html, split_message


async def send_weekly_reports(bot: Bot) -> None:
    """Iterates through all registered business profiles and delivers Sunday evening weekly report."""
    logger.info("Executing scheduled Weekly Report job...")
    profiles = await get_all_profiles()

    for profile in profiles:
        user_id = profile["user_id"]
        lang = profile.get("preferred_language", "kaa")

        try:
            summary = await get_tasks_summary_for_period(user_id=user_id, days=7)
            completed_count = summary["completed_count"]
            open_count = summary["open_count"]

            # Prompt Gemini
            prompt = (
                f"Búgin háptelik esabat waqtı (Ekshembi keshki 20:00). Paydalanıwshı kórsetkishleri:\n"
                f"- Usı háptede orınlanǵan tapsırmalar: {completed_count}\n"
                f"- Házirshe ashıq qalǵan tapsırmalar: {open_count}\n"
                f"- Paydalanıwshınıń usı aydagı baslı maqseti: {profile.get('main_goal_this_month', 'Kórsetilmegen')}\n\n"
                f"Kelesi hápte ushın qısqa, ruhlandırıwshı hám anıq strategiyalıq 3 másláhát beriń.\n"
                f"Juwap stili: kásiplik sherik sıpatında, qısqa, suwı joq, paydalanıwshı tilinde ({lang})."
            )

            response_raw = await gemini_service.generate_response(
                user_id=user_id,
                prompt_parts=prompt,
                profile=profile,
                mode="general",
                history=None
            )

            if lang == "ru":
                header = (
                    "📊 <b>Итоги недели и план на следующую:</b>\n\n"
                    f"✅ <b>Выполнено задач за неделю:</b> {completed_count}\n"
                    f"⏳ <b>Открытых задач:</b> {open_count}\n\n"
                    "💡 <b>Рекомендации на следующую неделю:</b>\n"
                )
            elif lang == "uz":
                header = (
                    "📊 <b>Hafta sarhisobi va kelgusi hafta rejasi:</b>\n\n"
                    f"✅ <b>Hafta davomida bajarilgan:</b> {completed_count}\n"
                    f"⏳ <b>Ochiq vazifalar:</b> {open_count}\n\n"
                    "💡 <b>Kelgusi hafta uchun tavsiyalar:</b>\n"
                )
            else:
                header = (
                    "📊 <b>Hápte juwmaǵı hám kelesi hápte rejeleri:</b>\n\n"
                    f"✅ <b>Háptede orınlanǵan tapsırmalar:</b> {completed_count}\n"
                    f"⏳ <b>Ashıq qalǵan tapsırmalar:</b> {open_count}\n\n"
                    "💡 <b>Kelesi hápte ushın sheriklik másláhátleri:</b>\n"
                )

            gemini_html = markdown_to_telegram_html(response_raw)
            full_text = header + gemini_html

            chunks = split_message(full_text)
            for chunk in chunks:
                await bot.send_message(chat_id=user_id, text=chunk, parse_mode="HTML")

            logger.info(f"Weekly report sent to user {user_id}")

        except Exception as e:
            logger.error(f"Failed to generate/send weekly report for user {user_id}: {e}", exc_info=True)
