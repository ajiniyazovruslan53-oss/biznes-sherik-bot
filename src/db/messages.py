"""
Messages database operations: per-user chat history and memory.
"""

from typing import List, Dict, Any
from src.db.database import get_db_connection


async def save_message(user_id: int, role: str, content: str) -> None:
    """Saves a message (user or model) into database."""
    async with get_db_connection() as db:
        await db.execute(
            """
            INSERT INTO messages (user_id, role, content)
            VALUES (?, ?, ?);
            """,
            (user_id, role, content)
        )
        await db.commit()


async def get_recent_messages(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Retrieves the last `limit` messages for user, in chronological order.
    Returns list of dicts: [{'role': 'user'|'model', 'content': '...'}]
    """
    async with get_db_connection() as db:
        async with db.execute(
            """
            SELECT role, content, timestamp
            FROM (
                SELECT role, content, timestamp
                FROM messages
                WHERE user_id = ?
                ORDER BY timestamp DESC, id DESC
                LIMIT ?
            )
            ORDER BY timestamp ASC;
            """,
            (user_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def clear_user_history(user_id: int) -> None:
    """Clears conversation history for user."""
    async with get_db_connection() as db:
        await db.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
        await db.commit()
