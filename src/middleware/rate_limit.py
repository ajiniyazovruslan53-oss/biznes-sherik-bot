"""
Rate limiting middleware: limits daily requests to DAILY_RATE_LIMIT per user.
Exempts admin and simple navigation commands if desired.
"""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message

from src.db.limits import check_and_increment_rate_limit
from src.db.profiles import get_profile
from src.utils.i18n import get_text
from src.config import config


class RateLimitMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        # Skip rate limit for admin commands or onboarding /start
        if event.text and event.text.startswith(("/start", "/add", "/remove", "/stats", "/profile", "/edit", "/tasks")):
            return await handler(event, data)

        profile = await get_profile(user.id)
        tz_name = profile.get("timezone", config.DEFAULT_TIMEZONE) if profile else config.DEFAULT_TIMEZONE
        lang = profile.get("preferred_language", "kaa") if profile else "kaa"

        allowed, current_count = await check_and_increment_rate_limit(
            user_id=user.id,
            limit=config.DAILY_RATE_LIMIT,
            tz_name=tz_name
        )

        if not allowed:
            limit_msg = get_text("rate_limit_exceeded", lang=lang)
            await event.answer(limit_msg, parse_mode="HTML")
            return None

        return await handler(event, data)
