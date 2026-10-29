"""
Tasks database operations: task management, reminders, and weekly summaries.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from src.db.database import get_db_connection


async def create_task(user_id: int, title: str, due_datetime: Optional[str] = None) -> int:
    """Inserts a new task and returns its generated ID."""
    clean_title = title.strip()
    clean_due = due_datetime.strip() if due_datetime else None

    async with get_db_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO tasks (user_id, title, due_datetime, status)
            VALUES (?, ?, ?, 'pending');
            """,
            (user_id, clean_title, clean_due)
        )
        await db.commit()
        return cursor.lastrowid


async def get_tasks(user_id: int, status: str = "pending") -> List[Dict[str, Any]]:
    """Retrieves tasks for a user filtered by status ('pending', 'completed', or 'all')."""
    async with get_db_connection() as db:
        if status == "all":
            query = "SELECT * FROM tasks WHERE user_id = ? ORDER BY id DESC"
            params = (user_id,)
        else:
            query = "SELECT * FROM tasks WHERE user_id = ? AND status = ? ORDER BY id ASC"
            params = (user_id, status)

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_task_by_id(task_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Retrieves a single task by ID."""
    async with get_db_connection() as db:
        if user_id is not None:
            query = "SELECT * FROM tasks WHERE id = ? AND user_id = ?"
            params = (task_id, user_id)
        else:
            query = "SELECT * FROM tasks WHERE id = ?"
            params = (task_id,)

        async with db.execute(query, params) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def complete_task(task_id: int, user_id: Optional[int] = None) -> bool:
    """Marks a task as completed."""
    async with get_db_connection() as db:
        if user_id is not None:
            query = "UPDATE tasks SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?"
            params = (task_id, user_id)
        else:
            query = "UPDATE tasks SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = ?"
            params = (task_id,)

        cursor = await db.execute(query, params)
        await db.commit()
        return cursor.rowcount > 0


async def reschedule_task(task_id: int, user_id: int, new_due_datetime: str) -> bool:
    """Updates due_datetime for a task."""
    async with get_db_connection() as db:
        cursor = await db.execute(
            "UPDATE tasks SET due_datetime = ? WHERE id = ? AND user_id = ?",
            (new_due_datetime, task_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0


async def delete_task(task_id: int, user_id: int) -> bool:
    """Deletes a task by ID."""
    async with get_db_connection() as db:
        cursor = await db.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_pending_tasks_with_due() -> List[Dict[str, Any]]:
    """Retrieves all pending tasks that have a due_datetime set (for restoring scheduler jobs)."""
    async with get_db_connection() as db:
        async with db.execute(
            """
            SELECT id, user_id, title, due_datetime
            FROM tasks
            WHERE status = 'pending' AND due_datetime IS NOT NULL
            ORDER BY due_datetime ASC;
            """
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_tasks_summary_for_period(user_id: int, days: int = 7) -> Dict[str, Any]:
    """Retrieves counts and details of completed vs open tasks for weekly report."""
    async with get_db_connection() as db:
        # Completed in the last `days` days
        async with db.execute(
            """
            SELECT COUNT(*) FROM tasks
            WHERE user_id = ? AND status = 'completed'
            AND completed_at >= datetime('now', ?)
            """,
            (user_id, f"-{days} days")
        ) as c:
            completed_count = (await c.fetchone())[0]

        # Currently open
        async with db.execute(
            """
            SELECT COUNT(*) FROM tasks
            WHERE user_id = ? AND status = 'pending'
            """,
            (user_id,)
        ) as c:
            open_count = (await c.fetchone())[0]

        # Fetch list of open tasks
        async with db.execute(
            """
            SELECT id, title, due_datetime FROM tasks
            WHERE user_id = ? AND status = 'pending'
            ORDER BY id ASC LIMIT 5
            """,
            (user_id,)
        ) as cursor:
            open_tasks = [dict(row) for row in await cursor.fetchall()]

    return {
        "completed_count": completed_count,
        "open_count": open_count,
        "open_sample": open_tasks,
    }
