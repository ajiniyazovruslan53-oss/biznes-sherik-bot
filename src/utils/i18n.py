"""
Internationalization (i18n) texts for Biznes Sherik bot:
Supports Karakalpak (kaa - Latin script with correct letters), Uzbek (uz), Russian (ru).
"""

from typing import Dict, Any

MESSAGES: Dict[str, Dict[str, str]] = {
    # Access control
    "access_denied": {
        "kaa": "Keshirersiz, bul bot tek kurs studentleri hám arnawlı qatnasıwshılar ushın mólsherlengen. Eger siz kurs studenti bolsańız, iltimas, kuratorıńızǵa Telegram ID-ńizdi jiberiń:\n<code>{user_id}</code>",
        "uz": "Kechirasiz, ushbu bot faqat kurs talabalari va maxsus ishtirokchilar uchun mo'ljallangan. Agar siz kurs talabasi bo'lsangiz, iltimos, kuratoringizga Telegram ID-ingizni yuboring:\n<code>{user_id}</code>",
        "ru": "Извините, этот бот предназначен только для студентов курса и закрытого клуба. Если вы студент, отправьте куратору ваш Telegram ID:\n<code>{user_id}</code>",
    },
    # Onboarding start
    "choose_language": {
        "kaa": "Assalawma áleykum! <b>Biznes Sherik</b> botına xosh kelipsiz!\nQaysı tilde sóyleseyik? / Tilni tanlang / Выберите язык:",
        "uz": "Assalomu alaykum! <b>Biznes Sherik</b> botiga xush kelibsiz!\nTilni tanlang / Qaysı tilde sóyleseyik? / Выберите язык:",
        "ru": "Здравствуйте! Добро пожаловать в <b>Biznes Sherik</b>!\nВыберите язык общения / Tilni tanlang:",
    },
    "welcome_onboarding": {
        "kaa": "Ájayıp! Men sizdiń jeke biznes járdemshińiz — sherigińiz bolaman.\nSizge anıq hám paydalı kómeklesiwim ushın biznesińiz haqqında bir neshe soraw beremen.\n\n1. <b>Atıńız kim?</b> (Sizge qalay múrájat eteyin?)",
        "uz": "Ajoyib! Men sizning shaxsiy biznes yordamchingiz — sherigingiz bo'laman.\nSizga aniq va amaliy yordam bera olishim uchun biznesingiz haqida bir nechta savol beraman.\n\n1. <b>Ismingiz nima?</b> (Sizga qanday murojaat qilay?)",
        "ru": "Отлично! Я ваш личный бизнес-ассистент и надёжный партнёр.\nЧтобы давать точные и практичные советы с учётом ваших реалий, задам несколько вопросов о вашем бизнесе.\n\n1. <b>Как вас зовут?</b>",
    },
    "ask_business_type": {
        "kaa": "2. <b>Biznesińiz qaysı baǵdarda?</b>\n(Mısalı: Hayal-qızlar kiyim dúkanı, qantlı ónimler/tort pısiriw, kofeixana, avto-xızmet h.t.b.)",
        "uz": "2. <b>Biznesingiz qaysi sohada?</b>\n(Masalan: Ayollar kiyimlari do'koni, qandolatchilik/tort pishirish, kofexona, avto-xizmat va h.k.)",
        "ru": "2. <b>В какой сфере ваш бизнес?</b>\n(Например: Магазин женской одежды, кондитерская/торты на заказ, кофейня, автосервис и т.д.)",
    },
    "ask_city": {
        "kaa": "3. <b>Qaysı qala yamasa rayonda isleysiz?</b>\n(Mısalı: Nókis, Xojeli, Qońırat, Shımbay, Tashkent h.t.b.)",
        "uz": "3. <b>Qaysi shahar yoki tumanda faoliyat yuritasiz?</b>\n(Masalan: Nukus, Toshkent, Xo'jayli, Qo'ng'irot va h.k.)",
        "ru": "3. <b>В каком городе или регионе вы работаете?</b>\n(Например: Нукус, Ташкент, Ходжейли, Кунград и т.д.)",
    },
    "ask_products_and_prices": {
        "kaa": "4. <b>Qanday ónim yamasa xızmetler satasız hám ortasha bahası qansha?</b>\n(Mısalı: Kóylekler 200 000 - 500 000 so'm, ortasha chek 350 000 so'm)",
        "uz": "4. <b>Qanday mahsulot yoki xizmatlar sotasiz va o'rtacha narxi qancha?</b>\n(Masalan: Ko'ylaklar 200 000 - 500 000 so'm, o'rtacha chek 350 000 so'm)",
        "ru": "4. <b>Какие товары или услуги продаете и каков средний чек/цены?</b>\n(Например: Платья 200 000 - 500 000 сум, средний чек 350 000 сум)",
    },
    "ask_target_customer": {
        "kaa": "5. <b>Sizdiń tiykarǵı klientlerińiz kimler?</b>\n(Mısalı: 20-35 jas aralıǵındaǵı hayal-qızlar, jas analar, studentler)",
        "uz": "5. <b>Sizning asosiy mijozlaringiz kimlar?</b>\n(Masalan: 20-35 yoshdagi ayollar, yosh onalar, talabalar)",
        "ru": "5. <b>Кто ваша целевая аудитория (покупатели)?</b>\n(Например: Женщины 20-35 лет, молодые мамы, студенты)",
    },
    "ask_sales_channels": {
        "kaa": "6. <b>Klientlerdi qayerden tabasız, sawda qaysı kanallarda ketedi?</b>\n(Mısalı: Instagram, Telegram kanal, oflayn dúkan, OLX, Uzum)",
        "uz": "6. <b>Mijozlarni qayerdan topasiz, savdo qaysi kanallarda ketadi?</b>\n(Masalan: Instagram, Telegram kanal, oflayn do'kon, OLX, Uzum)",
        "ru": "6. <b>Через какие каналы привлекаете клиентов и продаете?</b>\n(Например: Instagram, Telegram-канал, офлайн точка, OLX, Uzum)",
    },
    "ask_main_goal_this_month": {
        "kaa": "7. <b>Usı aydagı baslı maqsetińiz nima?</b>\n(Mısalı: Sawdanı 30 mln so'mǵa jetkeriw, 50 jańa turaqlı klient tabıw, sap paydanı 20% kóbeytiw)",
        "uz": "7. <b>Shu oydagi asosiy maqsadingiz nima?</b>\n(Masalan: Savdoni 30 mln so'mga yetkazish, 50 ta yangi doimiy mijoz, sof foydani 20% oshirish)",
        "ru": "7. <b>Какова ваша главная цель на этот месяц?</b>\n(Например: Выручка 30 млн сум, привлечь 50 новых постоянных клиентов, поднять чистую прибыль на 20%)",
    },
    "onboarding_complete": {
        "kaa": "✅ <b>Ráxmet! Biznes profilińiz to'liq saqlandı!</b>\n\nEndi men hár bir sorawıńızǵa anıq biznesińizdi, ónimlerińizdi hám maqsetińizdi esapqa alıp juwap beremen.\n\n<b>Múmkinshilikler:</b>\n• /profile — profildi kóriw\n• /edit — profildi ózgertiw\n• /tasks — wazıypalar hám esletpeler\n• /content — post hám Reels ssenariyleri\n• /reply — klient xatına satıwshı juwap jazıw\n• /calc — marja, payda hám zıyansızlıq esap-kitabı\n• /mentor — jańa ideyalardı analizlew\n• /general — ápiwayı rejimge qaytıw\n\n<i>Siz maǵan tekst, dawıslı xabar yamasa shek/baha súwretlerin jiberip baslay beriwińizge boladı!</i>",
        "uz": "✅ <b>Rahmat! Biznes profilingiz to'liq saqlandi!</b>\n\nEndi men har bir savolingizga aniq biznesingiz, mahsulotlaringiz va maqsadingizni hisobga olib javob beraman.\n\n<b>Imkoniyatlar:</b>\n• /profile — profilni ko'rish\n• /edit — profilni o'zgartirish\n• /tasks — vazifalar va eslatmalar\n• /content — post va Reels ssenariylari\n• /reply — mijoz xatiga sotuvchi javob yozish\n• /calc — marja, foyda va zararsizlik hisobi\n• /mentor — yangi g'oyalarni tahlil qilish\n• /general — umumiy rejimga qaytish\n\n<i>Siz menga matn, ovozli xabar yoki chek/narxlar rasmini yuborishingiz mumkin!</i>",
        "ru": "✅ <b>Спасибо! Профиль вашего бизнеса успешно сохранен!</b>\n\nТеперь каждый мой совет будет опираться на ваши реальные цифры, товары, город и цели.\n\n<b>Возможности:</b>\n• /profile — просмотр профиля\n• /edit — редактирование данных\n• /tasks — задачи и напоминания\n• /content — посты и сценарии Reels\n• /reply — продающие ответы на сообщения клиентов\n• /calc — расчёт маржи, прибыли и точки безубыточности\n• /mentor — честная оценка бизнес-идей\n• /general — возврат в общий режим\n\n<i>Вы можете писать мне текстом, отправлять голосовые сообщения или присылать фото чеков и ценников!</i>",
    },
    # Mode switch confirmations
    "mode_switched_general": {
        "kaa": "🎯 <b>Rejim: Tiykarǵı járdemshi (General)</b>\nBiznes haqqında qálegen sorawıńızdı beriń, kúnlik reje qurań yamasa máselelerdi sheshiń.",
        "uz": "🎯 <b>Rejim: Asosiy yordamchi (General)</b>\nBiznes bo'yicha istalgan savolingizni bering, kunlik reja tuzing yoki masalalarni hal qiling.",
        "ru": "🎯 <b>Режим: Основной ассистент (General)</b>\nЗадавайте любые вопросы по бизнесу, планируйте день или обсуждайте задачи.",
    },
    "mode_switched_content": {
        "kaa": "✍️ <b>Rejim: Kontent (Content)</b>\nQanday tema boyınsha post, Stories yamasa Reels ssenariysi kerek? Maǵan aytsańız, 2 túrli variant tayarlap beremen.",
        "uz": "✍️ <b>Rejim: Kontent (Content)</b>\nQanday mavzuda post, Stories yoki Reels ssenariysi kerak? Menga aytsangiz, 2 xil variant tayyorlab beraman.",
        "ru": "✍️ <b>Режим: Контент (Content)</b>\nНа какую тему нужен пост, Stories или сценарий Reels? Напишите, и я подготовлю 2 рабочих варианта.",
    },
    "mode_switched_reply": {
        "kaa": "💬 <b>Rejim: Klientke juwap (Reply)</b>\nKlient jazǵan xabardı yamasa sorawdı koshirip jiberiń. Men satıwdı jaqınlastıratuǵın hám e'tirozlardı sheshetuǵın 2 variant tayarlayman.",
        "uz": "💬 <b>Rejim: Mijozga javob (Reply)</b>\nMijoz yozgan xabarni yoki e'tirozni nusxalab yuboring. Sotuvni yakunlashga undovchi 2 ta chiroyli javob tayyorlayman.",
        "ru": "💬 <b>Режим: Ответ клиенту (Reply)</b>\nПерешлите или вставьте сообщение клиента. Я подготовлю вежливый ответ, снимающий возражения и ведущий к продаже (основной + короткий вариант).",
    },
    "mode_switched_calc": {
        "kaa": "🧮 <b>Rejim: Esap-kitap (Calc)</b>\nÓz bahasın (tannarx), satıw bahasın hám shıǵınlarıńızdı jiberiń. Marja, sap payda hám zıyansızlıq noqatın esaplap beremen.",
        "uz": "🧮 <b>Rejim: Hisob-kitob (Calc)</b>\nTannarx, sotish narxi va xarajatlaringizni yuboring. Marja, sof foyda va zararsizlik nuqtasini bosqichma-bosqich hisoblab beraman.",
        "ru": "🧮 <b>Режим: Расчёты (Calc)</b>\nУкажите себестоимость, цену продажи и постоянные расходы. Я пошагово рассчитаю маржу, наценку, прибыль и точку безубыточности.",
    },
    "mode_switched_mentor": {
        "kaa": "💡 <b>Rejim: Mentor (Mentor)</b>\nJańa biznes ideyańızdı jazıń. Onıń 3 kúshli tárepin, 3 qáwipin, 7 kúnde arzan sınaqtan ótkeriw jolların hám dáslepki 3 qádemdi anıq aytaman.",
        "uz": "💡 <b>Rejim: Mentor (Mentor)</b>\nYangi biznes g'oyangizni yozing. 3 ta kuchli tomoni, 3 ta xavfi, 7 kunda arzon test qilish va birinchi 3 qadamni aniq tahlil qilib beraman.",
        "ru": "💡 <b>Режим: Ментор (Mentor)</b>\nОпишите вашу идею. Я честно оценю 3 сильные стороны, 3 риска, как протестировать гипотезу за 7 дней и первые 3 практических шага.",
    },
    # Tasks
    "tasks_empty": {
        "kaa": "📝 Házirshe ashıq tapsırmalar joq. Jańa tapsırma qosıw ushın maǵan jazıń yamasa dawıs penen aytıń!",
        "uz": "📝 Hozircha ochiq vazifalar yo'q. Yangi vazifa qo'shish uchun menga yozing yoki ovoz bilan ayting!",
        "ru": "📝 Открытых задач пока нет. Чтобы добавить задачу, просто напишите мне или скажите голосом!",
    },
    "tasks_header": {
        "kaa": "📋 <b>Sizdiń tapsırmalarıńız:</b>\n",
        "uz": "📋 <b>Sizning vazifalaringiz:</b>\n",
        "ru": "📋 <b>Ваши текущие задачи:</b>\n",
    },
    # Rate limit
    "rate_limit_exceeded": {
        "kaa": "⏳ <b>Kúnlik limit tawsıldı (50 soraw).</b>\nSiz kúnlik limitke jettińiz. Quota túnde (00:00 de) jańalanadı. Erteńge shekem!",
        "uz": "⏳ <b>Kunlik limit tugadi (50 ta so'rov).</b>\nSiz kunlik limitga yetdingiz. Quota yarim tunda (00:00 da) yangilanadi. Ertagacha!",
        "ru": "⏳ <b>Дневной лимит исчерпан (50 запросов).</b>\nВы использовали дневную квоту. Лимит обновится в полночь (00:00). До завтра!",
    },
    # Timeout / Error
    "timeout_error": {
        "kaa": "⚠️ Keshirersiz, serverden juwap kútiw waqtı tawsıldı (60 sek). Iltimas, bir azdan soń qaytadan urınıp kóriń.",
        "uz": "⚠️ Kechirasiz, serverdan javob kutish vaqti tugadi (60 sek). Iltimos, birozdan so'ng qayta urinib ko'ring.",
        "ru": "⚠️ Извините, время ожидания ответа истекло (60 сек). Пожалуйста, повторите запрос чуть позже.",
    },
    "general_error": {
        "kaa": "⚠️ Keshirersiz, qátelik júz berdi. Qaytadan urınıp kóriń.",
        "uz": "⚠️ Kechirasiz, xatolik yuz berdi. Qayta urinib ko'ring.",
        "ru": "⚠️ Произошла непредвиденная ошибка. Пожалуйста, попробуйте еще раз.",
    },
}


def get_text(key: str, lang: str = "kaa", **kwargs: Any) -> str:
    """Retrieves localized text with fallback to 'kaa' or 'ru'."""
    entry = MESSAGES.get(key, {})
    text = entry.get(lang) or entry.get("kaa") or entry.get("ru") or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
