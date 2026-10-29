"""Handlers package for Biznes Sherik bot."""
from aiogram import Dispatcher

from src.handlers.admin import router as admin_router
from src.handlers.onboarding import router as onboarding_router
from src.handlers.modes import router as modes_router
from src.handlers.tasks import router as tasks_router
from src.handlers.voice import router as voice_router
from src.handlers.photo import router as photo_router
from src.handlers.chat import router as chat_router


def register_all_handlers(dp: Dispatcher) -> None:
    """Registers all handler routers in appropriate priority order."""
    dp.include_router(admin_router)
    dp.include_router(onboarding_router)
    dp.include_router(modes_router)
    dp.include_router(tasks_router)
    dp.include_router(voice_router)
    dp.include_router(photo_router)
    dp.include_router(chat_router)
