"""Database module for Biznes Sherik bot."""
from src.db.database import init_db, get_db_connection
from src.db.access import is_user_allowed, add_allowed_user, remove_allowed_user, list_allowed_users, get_system_stats
from src.db.profiles import get_profile, upsert_profile, update_profile_field, get_all_profiles, format_profile_for_prompt, format_profile_display
from src.db.messages import save_message, get_recent_messages, clear_user_history
from src.db.tasks import create_task, get_tasks, get_task_by_id, complete_task, reschedule_task, delete_task, get_pending_tasks_with_due, get_tasks_summary_for_period
from src.db.limits import check_and_increment_rate_limit

__all__ = [
    "init_db",
    "get_db_connection",
    "is_user_allowed",
    "add_allowed_user",
    "remove_allowed_user",
    "list_allowed_users",
    "get_system_stats",
    "get_profile",
    "upsert_profile",
    "update_profile_field",
    "get_all_profiles",
    "format_profile_for_prompt",
    "format_profile_display",
    "save_message",
    "get_recent_messages",
    "clear_user_history",
    "create_task",
    "get_tasks",
    "get_task_by_id",
    "complete_task",
    "reschedule_task",
    "delete_task",
    "get_pending_tasks_with_due",
    "get_tasks_summary_for_period",
    "check_and_increment_rate_limit",
]
