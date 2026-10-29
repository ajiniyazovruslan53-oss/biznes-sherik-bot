"""
Unit tests for task parsing, task database operations, and function calling tools.
"""

import pytest
import os
import uuid
from pathlib import Path
from datetime import datetime
import zoneinfo

from src.config import config
from src.db.database import init_db
from src.db.tasks import create_task, get_tasks, complete_task, delete_task, get_task_by_id
from src.scheduler.reminders import parse_datetime
from src.gemini.tools import execute_tool_call


@pytest.fixture(autouse=True)
async def setup_test_db(monkeypatch, tmp_path):
    """Initializes a fresh isolated SQLite DB in pytest tmp_path for each test."""
    test_db = tmp_path / f"test_tasks_{uuid.uuid4().hex}.db"
    monkeypatch.setattr(config, "DB_PATH", str(test_db))
    await init_db()
    yield
    try:
        if test_db.exists():
            test_db.unlink()
    except Exception:
        pass


def test_parse_datetime_iso_and_formats():
    tz = zoneinfo.ZoneInfo("Asia/Tashkent")

    # Format 1: YYYY-MM-DD HH:MM:SS
    dt1 = parse_datetime("2026-11-10 15:30:00")
    assert dt1 is not None
    assert dt1.year == 2026
    assert dt1.month == 11
    assert dt1.day == 10
    assert dt1.hour == 15
    assert dt1.minute == 30
    assert dt1.tzinfo == tz

    # Format 2: YYYY-MM-DDTHH:MM
    dt2 = parse_datetime("2026-12-01T09:45")
    assert dt2 is not None
    assert dt2.hour == 9
    assert dt2.minute == 45

    # Format 3: Date only defaults to 09:00 AM
    dt3 = parse_datetime("2026-11-15")
    assert dt3 is not None
    assert dt3.day == 15
    assert dt3.hour == 9
    assert dt3.minute == 0

    # Format 4: Invalid date
    dt4 = parse_datetime("invalid-string")
    assert dt4 is None


@pytest.mark.asyncio
async def test_task_db_crud():
    user_id = 999111
    task_id = await create_task(user_id=user_id, title="Klientke xat jiberiw", due_datetime="2026-11-01 10:00:00")
    assert task_id > 0

    task = await get_task_by_id(task_id, user_id=user_id)
    assert task is not None
    assert task["title"] == "Klientke xat jiberiw"
    assert task["status"] == "pending"

    tasks = await get_tasks(user_id=user_id, status="pending")
    assert len(tasks) == 1

    # Complete task
    success = await complete_task(task_id=task_id, user_id=user_id)
    assert success is True

    pending_after = await get_tasks(user_id=user_id, status="pending")
    assert len(pending_after) == 0

    completed_after = await get_tasks(user_id=user_id, status="completed")
    assert len(completed_after) == 1

    # Delete task
    del_ok = await delete_task(task_id=task_id, user_id=user_id)
    assert del_ok is True
    assert (await get_task_by_id(task_id, user_id=user_id)) is None


@pytest.mark.asyncio
async def test_execute_tool_call_add_and_complete_task():
    user_id = 888222
    callback_invocations = []

    async def mock_scheduler_cb(t_id, u_id, title, due):
        callback_invocations.append((t_id, u_id, title, due))

    # Add task tool call
    res_add = await execute_tool_call(
        name="add_task",
        args={"title": "Instagram Reels túsiriw", "due_datetime": "2026-11-05 18:00:00"},
        user_id=user_id,
        scheduler_callback=mock_scheduler_cb
    )
    assert res_add["status"] == "success"
    task_id = res_add["task_id"]
    assert len(callback_invocations) == 1
    assert callback_invocations[0][0] == task_id

    # List tasks tool call
    res_list = await execute_tool_call(
        name="list_tasks",
        args={"status": "pending"},
        user_id=user_id
    )
    assert res_list["status"] == "success"
    assert res_list["tasks_count"] == 1
    assert res_list["tasks"][0]["title"] == "Instagram Reels túsiriw"

    # Complete task tool call
    res_complete = await execute_tool_call(
        name="complete_task",
        args={"task_id": task_id},
        user_id=user_id
    )
    assert res_complete["status"] == "success"

    # Verify pending is empty
    res_list_after = await execute_tool_call(
        name="list_tasks",
        args={"status": "pending"},
        user_id=user_id
    )
    assert res_list_after["tasks_count"] == 0
