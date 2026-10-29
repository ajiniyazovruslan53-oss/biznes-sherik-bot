"""
Profiles database operations: user business profile storage, retrieval, and prompt formatting.
"""

from typing import Optional, Dict, Any, List
from src.db.database import get_db_connection


async def get_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves user's business profile."""
    async with get_db_connection() as db:
        async with db.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def upsert_profile(user_id: int, data: Dict[str, Any]) -> None:
    """Inserts or updates user's business profile."""
    async with get_db_connection() as db:
        await db.execute(
            """
            INSERT INTO profiles (
                user_id, name, business_type, city, products_and_prices,
                target_customer, sales_channels, main_goal_this_month,
                preferred_language, current_mode, timezone, updated_at
            ) VALUES (
                :user_id, :name, :business_type, :city, :products_and_prices,
                :target_customer, :sales_channels, :main_goal_this_month,
                :preferred_language, :current_mode, :timezone, CURRENT_TIMESTAMP
            )
            ON CONFLICT(user_id) DO UPDATE SET
                name = excluded.name,
                business_type = excluded.business_type,
                city = excluded.city,
                products_and_prices = excluded.products_and_prices,
                target_customer = excluded.target_customer,
                sales_channels = excluded.sales_channels,
                main_goal_this_month = excluded.main_goal_this_month,
                preferred_language = COALESCE(excluded.preferred_language, profiles.preferred_language),
                current_mode = COALESCE(excluded.current_mode, profiles.current_mode),
                timezone = COALESCE(excluded.timezone, profiles.timezone),
                updated_at = CURRENT_TIMESTAMP;
            """,
            {
                "user_id": user_id,
                "name": data.get("name", ""),
                "business_type": data.get("business_type", ""),
                "city": data.get("city", ""),
                "products_and_prices": data.get("products_and_prices", ""),
                "target_customer": data.get("target_customer", ""),
                "sales_channels": data.get("sales_channels", ""),
                "main_goal_this_month": data.get("main_goal_this_month", ""),
                "preferred_language": data.get("preferred_language", "kaa"),
                "current_mode": data.get("current_mode", "general"),
                "timezone": data.get("timezone", "Asia/Tashkent"),
            }
        )
        await db.commit()


async def update_profile_field(user_id: int, field_name: str, value: Any) -> None:
    """Updates a single field in user profile."""
    allowed_fields = {
        "name", "business_type", "city", "products_and_prices",
        "target_customer", "sales_channels", "main_goal_this_month",
        "preferred_language", "current_mode", "timezone"
    }
    if field_name not in allowed_fields:
        raise ValueError(f"Invalid profile field: {field_name}")

    async with get_db_connection() as db:
        await db.execute(
            f"UPDATE profiles SET {field_name} = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            (value, user_id)
        )
        await db.commit()


async def get_all_profiles() -> List[Dict[str, Any]]:
    """Retrieves all business profiles (for daily brief & weekly reports)."""
    async with get_db_connection() as db:
        async with db.execute("SELECT * FROM profiles ORDER BY user_id") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


def format_profile_for_prompt(profile: Optional[Dict[str, Any]]) -> str:
    """Formats business profile for injection into Gemini system instruction."""
    if not profile:
        return "Biznes profili ele toltırılmaǵan (jańa paydalanıwshı)."

    return f"""Atı / Имя: {profile.get('name', 'Kórsetilmegen')}
Biznes baǵdarı / Сфера: {profile.get('business_type', 'Kórsetilmegen')}
Qala yamasa rayon / Город: {profile.get('city', 'Kórsetilmegen')}
Ónimler hám bahaları / Товары и цены: {profile.get('products_and_prices', 'Kórsetilmegen')}
Tiykarǵı klientler / Целевая аудитория: {profile.get('target_customer', 'Kórsetilmegen')}
Satıw kanalları / Каналы продаж: {profile.get('sales_channels', 'Kórsetilmegen')}
Usı aydagı baslı maqset / Цель на месяц: {profile.get('main_goal_this_month', 'Kórsetilmegen')}
Qálewli til / Язык: {profile.get('preferred_language', 'kaa')}
Waqıt zonası / Timezone: {profile.get('timezone', 'Asia/Tashkent')}"""


def format_profile_display(profile: Dict[str, Any]) -> str:
    """Formats business profile for user display in /profile."""
    lang = profile.get("preferred_language", "kaa")
    
    if lang == "ru":
        return f"""💼 <b>Профиль вашего бизнеса</b>

👤 <b>Имя:</b> {profile.get('name', '-')}
🏢 <b>Сфера:</b> {profile.get('business_type', '-')}
📍 <b>Город:</b> {profile.get('city', '-')}
💰 <b>Товары и цены:</b> {profile.get('products_and_prices', '-')}
🎯 <b>Клиенты:</b> {profile.get('target_customer', '-')}
📣 <b>Каналы продаж:</b> {profile.get('sales_channels', '-')}
🚀 <b>Главная цель на месяц:</b> {profile.get('main_goal_this_month', '-')}
🌐 <b>Язык:</b> {profile.get('preferred_language', 'ru')}
⏰ <b>Часовой пояс:</b> {profile.get('timezone', 'Asia/Tashkent')}

<i>Чтобы изменить данные, введите /edit</i>"""
    elif lang == "uz":
        return f"""💼 <b>Biznes profilingiz</b>

👤 <b>Ism:</b> {profile.get('name', '-')}
🏢 <b>Soha:</b> {profile.get('business_type', '-')}
📍 <b>Shahar:</b> {profile.get('city', '-')}
💰 <b>Mahsulotlar va narxlar:</b> {profile.get('products_and_prices', '-')}
🎯 <b>Mijozlar:</b> {profile.get('target_customer', '-')}
📣 <b>Savdo kanallari:</b> {profile.get('sales_channels', '-')}
🚀 <b>Oylik asosiy maqsad:</b> {profile.get('main_goal_this_month', '-')}
🌐 <b>Til:</b> {profile.get('preferred_language', 'uz')}
⏰ <b>Vaqt mintaqasi:</b> {profile.get('timezone', 'Asia/Tashkent')}

<i>Ma'lumotlarni o'zgartirish uchun /edit buyrug'ini bering</i>"""
    else:  # Karakalpak default
        return f"""💼 <b>Biznes profilińiz</b>

👤 <b>Atıńız:</b> {profile.get('name', '-')}
🏢 <b>Biznes baǵdarı:</b> {profile.get('business_type', '-')}
📍 <b>Qala/rayon:</b> {profile.get('city', '-')}
💰 <b>Ónimler hám bahalar:</b> {profile.get('products_and_prices', '-')}
🎯 <b>Klientler:</b> {profile.get('target_customer', '-')}
📣 <b>Satıw kanalları:</b> {profile.get('sales_channels', '-')}
🚀 <b>Aylıq baslı maqset:</b> {profile.get('main_goal_this_month', '-')}
🌐 <b>Til:</b> {profile.get('preferred_language', 'kaa')}
⏰ <b>Waqıt zonası:</b> {profile.get('timezone', 'Asia/Tashkent')}

<i>Maǵlıwmatlardı ózgertiw ushın /edit buyrıǵın jiberiń</i>"""
