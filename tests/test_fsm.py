"""
Unit tests for Onboarding FSM states, data aggregation, and profile persistence.
"""

import pytest
import os
import uuid
from pathlib import Path
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey

from src.config import config
from src.db.database import init_db
from src.db.profiles import get_profile, upsert_profile, format_profile_for_prompt
from src.handlers.onboarding import OnboardingFSM


@pytest.fixture(autouse=True)
async def setup_test_db(monkeypatch, tmp_path):
    """Initializes a fresh isolated SQLite DB in pytest tmp_path for each test."""
    test_db = tmp_path / f"test_fsm_{uuid.uuid4().hex}.db"
    monkeypatch.setattr(config, "DB_PATH", str(test_db))
    await init_db()
    yield
    try:
        if test_db.exists():
            test_db.unlink()
    except Exception:
        pass


@pytest.mark.asyncio
async def test_onboarding_fsm_flow():
    storage = MemoryStorage()
    bot_id = 123456789
    user_id = 555777
    chat_id = 555777

    key = StorageKey(bot_id=bot_id, chat_id=chat_id, user_id=user_id)
    state = FSMContext(storage=storage, key=key)

    # 1. Start onboarding: waiting_for_language
    await state.set_state(OnboardingFSM.waiting_for_language)
    assert await state.get_state() == OnboardingFSM.waiting_for_language.state

    # 2. Select language
    await state.update_data(preferred_language="kaa")
    await state.set_state(OnboardingFSM.waiting_for_name)
    assert await state.get_state() == OnboardingFSM.waiting_for_name.state

    # 3. Enter Name
    await state.update_data(name="Aydos")
    await state.set_state(OnboardingFSM.waiting_for_business_type)

    # 4. Enter Business Type
    await state.update_data(business_type="Kiyim dúkani")
    await state.set_state(OnboardingFSM.waiting_for_city)

    # 5. Enter City
    await state.update_data(city="Nókis")
    await state.set_state(OnboardingFSM.waiting_for_products_and_prices)

    # 6. Enter Products and Prices
    await state.update_data(products_and_prices="Kóylekler 250 000 - 450 000 so'm")
    await state.set_state(OnboardingFSM.waiting_for_target_customer)

    # 7. Enter Target Customer
    await state.update_data(target_customer="20-35 jas hayal-qızlar")
    await state.set_state(OnboardingFSM.waiting_for_sales_channels)

    # 8. Enter Sales Channels
    await state.update_data(sales_channels="Instagram, Telegram kanal")
    await state.set_state(OnboardingFSM.waiting_for_main_goal_this_month)

    # 9. Enter Main Goal
    await state.update_data(main_goal_this_month="Aylıq 20 mln so'm sap paydaǵa shıǵıw")

    # Complete: persist to database
    final_data = await state.get_data()
    await upsert_profile(user_id=user_id, data=final_data)
    await state.clear()

    # Verify state is cleared
    assert await state.get_state() is None

    # Verify profile was correctly saved in DB
    profile = await get_profile(user_id)
    assert profile is not None
    assert profile["name"] == "Aydos"
    assert profile["business_type"] == "Kiyim dúkani"
    assert profile["city"] == "Nókis"
    assert profile["products_and_prices"] == "Kóylekler 250 000 - 450 000 so'm"
    assert profile["target_customer"] == "20-35 jas hayal-qızlar"
    assert profile["sales_channels"] == "Instagram, Telegram kanal"
    assert profile["main_goal_this_month"] == "Aylıq 20 mln so'm sap paydaǵa shıǵıw"
    assert profile["preferred_language"] == "kaa"
    assert profile["current_mode"] == "general"

    # Verify prompt formatting includes all fields
    prompt_snippet = format_profile_for_prompt(profile)
    assert "Aydos" in prompt_snippet
    assert "Kiyim dúkani" in prompt_snippet
    assert "Nókis" in prompt_snippet
    assert "20 mln so'm" in prompt_snippet
