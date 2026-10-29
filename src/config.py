"""
Configuration module for Biznes Sherik bot.
Loads environment variables and validates essential configurations.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")


class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    
    # Parse ADMIN_ID as int (or 0 if unset/invalid)
    _raw_admin_id = os.getenv("ADMIN_ID", "0").strip()
    ADMIN_ID: int = int(_raw_admin_id) if _raw_admin_id.isdigit() else 0
    
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    DAILY_RATE_LIMIT: int = int(os.getenv("DAILY_RATE_LIMIT", "50"))
    DB_PATH: str = os.getenv("DB_PATH", str(BASE_DIR / "biznes_sherik.db")).strip()
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").strip()
    DEFAULT_TIMEZONE: str = os.getenv("DEFAULT_TIMEZONE", "Asia/Tashkent").strip()
    REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))
    
    SYSTEM_PROMPT_PATH: Path = BASE_DIR / "prompts" / "system.md"

    @classmethod
    def validate(cls, check_secrets: bool = True) -> None:
        """Validate critical configuration fields."""
        if check_secrets:
            missing = []
            if not cls.BOT_TOKEN:
                missing.append("BOT_TOKEN")
            if not cls.GEMINI_API_KEY:
                missing.append("GEMINI_API_KEY")
            if not cls.ADMIN_ID:
                missing.append("ADMIN_ID")
            if missing:
                raise ValueError(f"Missing required environment variables in .env: {', '.join(missing)}")
        if not cls.SYSTEM_PROMPT_PATH.exists():
            raise FileNotFoundError(f"System prompt file not found at {cls.SYSTEM_PROMPT_PATH}")


config = Config()
