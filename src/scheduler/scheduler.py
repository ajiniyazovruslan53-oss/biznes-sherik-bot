"""
APScheduler orchestrator for Biznes Sherik bot.
Handles:
- Daily brief at 08:00
- Weekly report Sunday at 20:00
- Persistent task reminders restored on startup
"""

from datetime import datetime
import zoneinfo
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from aiogram import Bot

from src.config import config
from src.utils.logger import logger
from src.scheduler.reminders import parse_datetime, send_task_reminder
from src.scheduler.daily_brief import send_daily_briefs
from src.scheduler.weekly_report import send_weekly_reports
from src.db.tasks import get_pending_tasks_with_due


class BotScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=config.DEFAULT_TIMEZONE)
        self.bot: Optional[Bot] = None

    def start(self, bot: Bot) -> None:
        """Starts the scheduler and registers recurring jobs."""
        self.bot = bot

        # 1. Daily brief at 08:00 (Asia/Tashkent)
        self.scheduler.add_job(
            send_daily_briefs,
            trigger=CronTrigger(hour=8, minute=0, timezone=config.DEFAULT_TIMEZONE),
            args=[bot],
            id="daily_brief_job",
            replace_existing=True
        )

        # 2. Weekly report Sunday at 20:00 (Asia/Tashkent)
        self.scheduler.add_job(
            send_weekly_reports,
            trigger=CronTrigger(day_of_week="sun", hour=20, minute=0, timezone=config.DEFAULT_TIMEZONE),
            args=[bot],
            id="weekly_report_job",
            replace_existing=True
        )

        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("APScheduler started successfully.")

    async def restore_task_reminders(self, bot: Bot) -> None:
        """Restores pending task reminders from database on bot restart."""
        pending_reminders = await get_pending_tasks_with_due()
        tz = zoneinfo.ZoneInfo(config.DEFAULT_TIMEZONE)
        now = datetime.now(tz)
        restored_count = 0

        for task in pending_reminders:
            due_dt = parse_datetime(task["due_datetime"], config.DEFAULT_TIMEZONE)
            if due_dt and due_dt > now:
                self.schedule_reminder(
                    task_id=task["id"],
                    user_id=task["user_id"],
                    title=task["title"],
                    due_dt=due_dt
                )
                restored_count += 1

        logger.info(f"Restored {restored_count} task reminders on startup.")

    def schedule_reminder(
        self,
        task_id: int,
        user_id: int,
        title: str,
        due_dt: datetime
    ) -> None:
        """Schedules a one-off reminder notification for a specific task."""
        if not self.bot:
            logger.warning("Bot instance not set in scheduler; cannot schedule reminder.")
            return

        job_id = f"task_reminder_{task_id}"
        self.scheduler.add_job(
            send_task_reminder,
            trigger=DateTrigger(run_date=due_dt),
            args=[self.bot, task_id, user_id, title],
            id=job_id,
            replace_existing=True
        )
        logger.info(f"Scheduled reminder job '{job_id}' for {due_dt}")

    def cancel_reminder(self, task_id: int) -> None:
        """Cancels a scheduled task reminder job if it exists."""
        job_id = f"task_reminder_{task_id}"
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed reminder job '{job_id}'")
        except Exception:
            pass


bot_scheduler = BotScheduler()
