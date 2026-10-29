"""
Access control database operations: allowed_users check and admin commands.
"""

from typing import List, Dict, Any, Optional
from src.config import config
from src.db.database import get_db_connection


async def is_user_allowed(user_id: int) -> bool:
    """Checks if user is ADMIN_ID or exists in allowed_users table."""
    if user_id == config.ADMIN_ID and config.ADMIN_ID != 0:
        return True

    async with get_db_connection() as db:
        async with db.execute("SELECT 1 FROM allowed_users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row is not None


async def add_allowed_user(user_id: int, added_by: int, notes: str = "") -> bool:
    """Adds a student's Telegram ID to allowed_users."""
    async with get_db_connection() as db:
        await db.execute(
            """
            INSERT INTO allowed_users (user_id, added_by, notes)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET notes = excluded.notes;
            """,
            (user_id, added_by, notes)
        )
        await db.commit()
        return True


async def remove_allowed_user(user_id: int) -> bool:
    """Removes a user from allowed_users."""
    async with get_db_connection() as db:
        cursor = await db.execute("DELETE FROM allowed_users WHERE user_id = ?", (user_id,))
        await db.commit()
        return cursor.rowcount > 0


async def list_allowed_users() -> List[Dict[str, Any]]:
    """Lists all allowed users."""
    async with get_db_connection() as db:
        async with db.execute("SELECT user_id, added_by, notes, created_at FROM allowed_users ORDER BY created_at DESC") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_system_stats() -> Dict[str, Any]:
    """Gathers overall statistics for /stats command."""
    async with get_db_connection() as db:
        async with db.execute("SELECT COUNT(*) FROM allowed_users") as c:
            allowed_count = (await c.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM profiles") as c:
            profiles_count = (await c.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'") as c:
            pending_tasks = (await c.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM tasks WHERE status = 'completed'") as c:
            completed_tasks = (await c.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM messages") as c:
            total_messages = (await c.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM messages WHERE date(timestamp) = date('now')") as c:
            today_messages = (await c.fetchone())[0]

    return {
        "allowed_users": allowed_count,
        "profiles_completed": profiles_count,
        "pending_tasks": pending_tasks,
        "completed_tasks": completed_tasks,
        "total_messages": total_messages,
        "today_messages": today_messages,
    }
