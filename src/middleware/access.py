"""
Access control middleware: checks if user is ADMIN or in allowed_users table.
"""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from src.db.access import is_user_allowed
from src.utils.i18n import get_text
from src.utils.logger import logger


class AccessMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        allowed = await is_user_allowed(user.id)
        if not allowed:
            logger.warning(f"Unauthorized access attempt by user_id={user.id} (@{user.username})")
            denied_msg = get_text("access_denied", lang="kaa", user_id=user.id)
            if isinstance(event, Message):
                await event.answer(denied_msg, parse_mode="HTML")
            elif isinstance(event, CallbackQuery):
                await event.answer("Keshirersiz, sizge ruqsat berilmegen.", show_alert=True)
            return None

        return await handler(event, data)
