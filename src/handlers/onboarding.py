"""
Onboarding FSM handlers: /start, step-by-step business profile questionnaire,
/profile display, and /edit profile modification.
"""

from typing import Dict, Any
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.db.profiles import get_profile, upsert_profile, update_profile_field, format_profile_display
from src.utils.i18n import get_text
from src.utils.logger import logger

router = Router(name="onboarding_router")


class OnboardingFSM(StatesGroup):
    waiting_for_language = State()
    waiting_for_name = State()
    waiting_for_business_type = State()
    waiting_for_city = State()
    waiting_for_products_and_prices = State()
    waiting_for_target_customer = State()
    waiting_for_sales_channels = State()
    waiting_for_main_goal_this_month = State()


class EditProfileFSM(StatesGroup):
    waiting_for_field_value = State()


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Returns inline buttons for language selection."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Qaraqalpaqsha", callback_data="lang:kaa"),
                InlineKeyboardButton(text="O'zbekcha", callback_data="lang:uz"),
                InlineKeyboardButton(text="Русский", callback_data="lang:ru"),
            ]
        ]
    )


def get_edit_keyboard(lang: str = "kaa") -> InlineKeyboardMarkup:
    """Returns buttons to choose which field to edit."""
    labels = {
        "kaa": {
            "name": "👤 Atı",
            "business_type": "🏢 Baǵdarı",
            "city": "📍 Qala",
            "products_and_prices": "💰 Ónimler & Bahalar",
            "target_customer": "🎯 Klientler",
            "sales_channels": "📣 Kanallar",
            "main_goal_this_month": "🚀 Maqset",
            "restart": "🔄 Tolıq qaytadan toltırıw",
        },
        "uz": {
            "name": "👤 Ism",
            "business_type": "🏢 Soha",
            "city": "📍 Shahar",
            "products_and_prices": "💰 Mahsulotlar & Narxlar",
            "target_customer": "🎯 Mijozlar",
            "sales_channels": "📣 Kanallar",
            "main_goal_this_month": "🚀 Maqsad",
            "restart": "🔄 To'liq qayta to'ldirish",
        },
        "ru": {
            "name": "👤 Имя",
            "business_type": "🏢 Сфера",
            "city": "📍 Город",
            "products_and_prices": "💰 Товары и цены",
            "target_customer": "🎯 Аудитория",
            "sales_channels": "📣 Каналы",
            "main_goal_this_month": "🚀 Цель",
            "restart": "🔄 Заполнить заново",
        }
    }
    l = labels.get(lang, labels["kaa"])
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=l["name"], callback_data="edit_field:name"),
                InlineKeyboardButton(text=l["business_type"], callback_data="edit_field:business_type"),
            ],
            [
                InlineKeyboardButton(text=l["city"], callback_data="edit_field:city"),
                InlineKeyboardButton(text=l["products_and_prices"], callback_data="edit_field:products_and_prices"),
            ],
            [
                InlineKeyboardButton(text=l["target_customer"], callback_data="edit_field:target_customer"),
                InlineKeyboardButton(text=l["sales_channels"], callback_data="edit_field:sales_channels"),
            ],
            [
                InlineKeyboardButton(text=l["main_goal_this_month"], callback_data="edit_field:main_goal_this_month"),
            ],
            [
                InlineKeyboardButton(text=l["restart"], callback_data="edit_restart"),
            ]
        ]
    )


@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext):
    """Entry point for /start command."""
    user_id = message.from_user.id
    profile = await get_profile(user_id)

    if profile and profile.get("name"):
        lang = profile.get("preferred_language", "kaa")
        mode = profile.get("current_mode", "general")
        name = profile.get("name", "")

        if lang == "ru":
            text = (
                f"👋 С возвращением, <b>{name}</b>!\n"
                f"Текущий режим: <b>{mode}</b>\n\n"
                "Чем могу помочь сегодня? Напишите вопрос, отправьте голосовое сообщение или фото ценника/чека.\n\n"
                "Быстрые команды: /tasks, /content, /reply, /calc, /mentor, /profile, /edit"
            )
        elif lang == "uz":
            text = (
                f"👋 Qaytganingiz bilan, <b>{name}</b>!\n"
                f"Joriy rejim: <b>{mode}</b>\n\n"
                "Bugun qanday yordam bera olaman? Savolingizni yozing, ovozli xabar yoki narx/chek rasmini yuboring.\n\n"
                "Tezkor buyruqlar: /tasks, /content, /reply, /calc, /mentor, /profile, /edit"
            )
        else:
            text = (
                f"👋 Qaytıwıńız benen, <b>{name}</b>!\n"
                f"Házirgi rejim: <b>{mode}</b>\n\n"
                "Búgin qanday kómek kerek? Sorawıńızdı jazıń, dawıslı xabar yamasa shek/baha súwretin jiberiń.\n\n"
                "Tez buyrıqlar: /tasks, /content, /reply, /calc, /mentor, /profile, /edit"
            )
        await message.answer(text, parse_mode="HTML")
        return

    # Start onboarding
    await state.set_state(OnboardingFSM.waiting_for_language)
    await message.answer(
        get_text("choose_language", "kaa"),
        reply_markup=get_language_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(OnboardingFSM.waiting_for_language, F.data.startswith("lang:"))
async def handle_language_choice(callback: CallbackQuery, state: FSMContext):
    """User picked language via inline buttons."""
    lang = callback.data.split(":")[1]
    await state.update_data(preferred_language=lang)
    await callback.answer()

    await state.set_state(OnboardingFSM.waiting_for_name)
    await callback.message.edit_text(
        get_text("welcome_onboarding", lang),
        parse_mode="HTML"
    )


@router.message(OnboardingFSM.waiting_for_name, F.text)
async def handle_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    data = await state.get_data()
    lang = data.get("preferred_language", "kaa")

    await state.set_state(OnboardingFSM.waiting_for_business_type)
    await message.answer(get_text("ask_business_type", lang), parse_mode="HTML")


@router.message(OnboardingFSM.waiting_for_business_type, F.text)
async def handle_business_type(message: Message, state: FSMContext):
    await state.update_data(business_type=message.text.strip())
    data = await state.get_data()
    lang = data.get("preferred_language", "kaa")

    await state.set_state(OnboardingFSM.waiting_for_city)
    await message.answer(get_text("ask_city", lang), parse_mode="HTML")


@router.message(OnboardingFSM.waiting_for_city, F.text)
async def handle_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text.strip())
    data = await state.get_data()
    lang = data.get("preferred_language", "kaa")

    await state.set_state(OnboardingFSM.waiting_for_products_and_prices)
    await message.answer(get_text("ask_products_and_prices", lang), parse_mode="HTML")


@router.message(OnboardingFSM.waiting_for_products_and_prices, F.text)
async def handle_products_and_prices(message: Message, state: FSMContext):
    await state.update_data(products_and_prices=message.text.strip())
    data = await state.get_data()
    lang = data.get("preferred_language", "kaa")

    await state.set_state(OnboardingFSM.waiting_for_target_customer)
    await message.answer(get_text("ask_target_customer", lang), parse_mode="HTML")


@router.message(OnboardingFSM.waiting_for_target_customer, F.text)
async def handle_target_customer(message: Message, state: FSMContext):
    await state.update_data(target_customer=message.text.strip())
    data = await state.get_data()
    lang = data.get("preferred_language", "kaa")

    await state.set_state(OnboardingFSM.waiting_for_sales_channels)
    await message.answer(get_text("ask_sales_channels", lang), parse_mode="HTML")


@router.message(OnboardingFSM.waiting_for_sales_channels, F.text)
async def handle_sales_channels(message: Message, state: FSMContext):
    await state.update_data(sales_channels=message.text.strip())
    data = await state.get_data()
    lang = data.get("preferred_language", "kaa")

    await state.set_state(OnboardingFSM.waiting_for_main_goal_this_month)
    await message.answer(get_text("ask_main_goal_this_month", lang), parse_mode="HTML")


@router.message(OnboardingFSM.waiting_for_main_goal_this_month, F.text)
async def handle_main_goal(message: Message, state: FSMContext):
    await state.update_data(main_goal_this_month=message.text.strip())
    data = await state.get_data()
    lang = data.get("preferred_language", "kaa")

    # Persist profile to database
    user_id = message.from_user.id
    await upsert_profile(user_id, data)
    await state.clear()

    logger.info(f"Onboarding completed for user_id={user_id}")
    await message.answer(get_text("onboarding_complete", lang), parse_mode="HTML")


@router.message(Command("profile"))
async def handle_profile(message: Message):
    """Displays the user's current business profile."""
    user_id = message.from_user.id
    profile = await get_profile(user_id)
    if not profile or not profile.get("name"):
        await message.answer("Siz ele profildi toltırmadıńız. Toltırıw ushın /start buyrıǵın jiberiń.")
        return

    text = format_profile_display(profile)
    await message.answer(text, parse_mode="HTML")


@router.message(Command("edit"))
async def handle_edit(message: Message):
    """Provides choices to edit specific profile fields."""
    user_id = message.from_user.id
    profile = await get_profile(user_id)
    lang = profile.get("preferred_language", "kaa") if profile else "kaa"

    prompt_text = {
        "ru": "Выберите поле, которое хотите обновить:",
        "uz": "O'zgartirmoqchi bo'lgan ma'lumotni tanlang:",
        "kaa": "Ózgertpekshi bolǵan maǵlıwmatıńızdı saylań:"
    }.get(lang, "Ózgertpekshi bolǵan maǵlıwmatıńızdı saylań:")

    await message.answer(prompt_text, reply_markup=get_edit_keyboard(lang))


@router.callback_query(F.data == "edit_restart")
async def handle_edit_restart(callback: CallbackQuery, state: FSMContext):
    """Restarts onboarding from scratch."""
    await callback.answer()
    await state.set_state(OnboardingFSM.waiting_for_language)
    await callback.message.edit_text(
        get_text("choose_language", "kaa"),
        reply_markup=get_language_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("edit_field:"))
async def handle_edit_field_pick(callback: CallbackQuery, state: FSMContext):
    """Prompts for new value of a specific field."""
    field_name = callback.data.split(":")[1]
    await callback.answer()
    await state.set_state(EditProfileFSM.waiting_for_field_value)
    await state.update_data(editing_field=field_name)

    field_labels = {
        "name": "Jańa atıńızdı jazıń:",
        "business_type": "Jańa biznes baǵdarıńızdı jazıń:",
        "city": "Jańa qala yamasa rayonıńızdı jazıń:",
        "products_and_prices": "Ónimler hám jańa bahalardı jazıń:",
        "target_customer": "Tiykarǵı klientler auditińizdi jazıń:",
        "sales_channels": "Jańa satıw kanallarıńızdı jazıń:",
        "main_goal_this_month": "Usı aydagı jańa baslı maqsetińizdi jazıń:",
    }
    label = field_labels.get(field_name, "Jańa maǵlıwmatıńızdı kiritiń:")
    await callback.message.edit_text(f"✏️ <b>{label}</b>", parse_mode="HTML")


@router.message(EditProfileFSM.waiting_for_field_value, F.text)
async def handle_save_edited_field(message: Message, state: FSMContext):
    """Saves the edited single field."""
    data = await state.get_data()
    field_name = data.get("editing_field")
    new_value = message.text.strip()
    user_id = message.from_user.id

    if field_name:
        await update_profile_field(user_id, field_name, new_value)
        profile = await get_profile(user_id)
        lang = profile.get("preferred_language", "kaa") if profile else "kaa"

        success_msg = {
            "ru": "✅ Данные успешно обновлены!",
            "uz": "✅ Ma'lumot muvaffaqiyatli yangilandi!",
            "kaa": "✅ Maǵlıwmat sátsiz jańalandı!"
        }.get(lang, "✅ Maǵlıwmat jańalandı!")

        await message.answer(success_msg)

    await state.clear()
