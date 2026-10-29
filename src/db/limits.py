"""
Rate limiting operations per user per day.
"""

from typing import Tuple
from datetime import datetime
import zoneinfo
from src.config import config
from src.db.database import get_db_connection


def get_current_date_in_tz(tz_name: str = "Asia/Tashkent") -> str:
    """Returns today's date formatted as YYYY-MM-DD in the given timezone."""
    try:
        tz = zoneinfo.ZoneInfo(tz_name)
    except Exception:
        tz = zoneinfo.ZoneInfo("Asia/Tashkent")
    return datetime.now(tz).strftime("%Y-%m-%d")


async def check_and_increment_rate_limit(
    user_id: int,
    limit: int = config.DAILY_RATE_LIMIT,
    tz_name: str = config.DEFAULT_TIMEZONE
) -> Tuple[bool, int]:
    """
    Checks if user is within the daily quota.
    If within quota, increments counter and returns (True, current_count).
    If exceeded, returns (False, current_count).
    Admin (config.ADMIN_ID) is exempt from rate limits.
    """
    if user_id == config.ADMIN_ID and config.ADMIN_ID != 0:
        return True, 0

    today = get_current_date_in_tz(tz_name)

    async with get_db_connection() as db:
        async with db.execute(
            "SELECT count FROM usage_limits WHERE user_id = ? AND date = ?",
            (user_id, today)
        ) as cursor:
            row = await cursor.fetchone()
            current_count = row[0] if row else 0

        if current_count >= limit:
            return False, current_count

        new_count = current_count + 1
        await db.execute(
            """
            INSERT INTO usage_limits (user_id, date, count)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET count = excluded.count;
            """,
            (user_id, today, new_count)
        )
        await db.commit()
        return True, new_count
