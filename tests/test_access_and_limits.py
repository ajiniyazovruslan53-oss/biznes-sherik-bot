"""
Unit tests for access control whitelist, admin stats, and rate limiting logic.
"""

import pytest
import uuid
from src.config import config
from src.db.database import init_db
from src.db.access import is_user_allowed, add_allowed_user, remove_allowed_user, get_system_stats, list_allowed_users
from src.db.limits import check_and_increment_rate_limit
from src.gemini.client import gemini_service


@pytest.fixture(autouse=True)
async def setup_test_db(monkeypatch, tmp_path):
    """Initializes a fresh isolated SQLite DB in pytest tmp_path for each test."""
    test_db = tmp_path / f"test_access_{uuid.uuid4().hex}.db"
    monkeypatch.setattr(config, "DB_PATH", str(test_db))
    monkeypatch.setattr(config, "ADMIN_ID", 999999)
    await init_db()
    yield
    try:
        if test_db.exists():
            test_db.unlink()
    except Exception:
        pass


@pytest.mark.asyncio
async def test_admin_is_always_allowed():
    admin_id = 999999
    assert await is_user_allowed(admin_id) is True


@pytest.mark.asyncio
async def test_access_whitelist_flow():
    student_id = 123456
    # Not allowed initially
    assert await is_user_allowed(student_id) is False

    # Admin adds student
    await add_allowed_user(student_id, added_by=999999, notes="Kursant 1-potok")
    assert await is_user_allowed(student_id) is True

    users = await list_allowed_users()
    assert len(users) == 1
    assert users[0]["user_id"] == student_id
    assert users[0]["notes"] == "Kursant 1-potok"

    # Remove student
    assert await remove_allowed_user(student_id) is True
    assert await is_user_allowed(student_id) is False


@pytest.mark.asyncio
async def test_daily_rate_limiting():
    user_id = 777111
    limit = 3

    # 1st request
    ok, count = await check_and_increment_rate_limit(user_id=user_id, limit=limit)
    assert ok is True
    assert count == 1

    # 2nd request
    ok, count = await check_and_increment_rate_limit(user_id=user_id, limit=limit)
    assert ok is True
    assert count == 2

    # 3rd request (hits limit)
    ok, count = await check_and_increment_rate_limit(user_id=user_id, limit=limit)
    assert ok is True
    assert count == 3

    # 4th request (rejected)
    ok, count = await check_and_increment_rate_limit(user_id=user_id, limit=limit)
    assert ok is False
    assert count == 3

    # Admin is exempt
    admin_ok, _ = await check_and_increment_rate_limit(user_id=999999, limit=limit)
    assert admin_ok is True


def test_should_enable_search_conditions():
    # In mentor mode, search should always be enabled
    assert gemini_service.should_enable_search("mentor", "Biznes ideya bar") is True

    # In general mode, enabled only if asking for prices/trends/competitors
    assert gemini_service.should_enable_search("general", "Nókiste kóyleklerdiń házirgi bahası qansha?") is True
    assert gemini_service.should_enable_search("general", "Instagramda qanday jańa trendlar bar?") is True
    assert gemini_service.should_enable_search("general", "Búgingi jumıs rejemdi dúzip ber") is False
