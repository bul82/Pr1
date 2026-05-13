from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards import back_to_menu_kb
from bot.verification import verify_shop, format_verification_report, check_authenticity
from bot.database import add_shop, update_shop_verification, get_shop_by_url

router = Router()

verify_states = {}


@router.callback_query(lambda c: c.data == "verify_shop")
async def verify_shop_start(callback: CallbackQuery):
    verify_states[callback.from_user.id] = {"waiting_url": True}
    await callback.message.edit_text(
        "✅ Проверка магазина\n\n"
        "Введите URL магазина для проверки:\n"
        "Пример: https://example.ru"
    )


@router.callback_query(lambda c: c.data == "check_authenticity")
async def check_authenticity_start(callback: CallbackQuery):
    verify_states[callback.from_user.id] = {"waiting_auth": True}
    await callback.message.edit_text(
        "🔐 Проверка оригинальности\n\n"
        "Введите название товара и цену для проверки:\n"
        "Пример: Спиннинг Shimano, 5000"
    )


@router.message(F.text & ~F.text.startswith("/"))
async def handle_verify(message: Message):
    user_id = message.from_user.id
    state = verify_states.get(user_id, {})

    if state.get("waiting_url"):
        url = message.text.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        await message.answer(f"🔄 Проверяю магазин {url}...")

        try:
            shop = get_shop_by_url(url)
            if not shop:
                shop_id = add_shop("Unknown Shop", url)
                shop = {"id": shop_id, "name": "Unknown Shop"}

            result = await verify_shop(url)
            update_shop_verification(shop["id"], result)

            report = format_verification_report({
                "name": shop.get("name", "Магазин"),
                "rating": result.get("rating", 0),
                "verified": result.get("verified", 0),
                "checks_detail": result.get("checks_detail", {}),
            })

            await message.answer(report or "⚠️ Ошибка проверки")
        except Exception as e:
            await message.answer(f"⚠️ Ошибка: {e}")

        verify_states[user_id] = {}

    elif state.get("waiting_auth"):
        parts = message.text.split(",")
        if len(parts) >= 2:
            gear_name = parts[0].strip()
            try:
                price = float(parts[1].strip().replace("₽", "").replace(" ", ""))
            except:
                price = 0

            result = check_authenticity(gear_name, price, "")

            if result["is_suspicious"]:
                text = "⚠️ <b>Возможны признаки подделки:</b>\n\n"
                for issue in result["issues"]:
                    text += f"• {issue}\n"
                text += "\n📋 <b>Чек-лист проверки:</b>\n"
                for rec in result["checklist"]:
                    text += f"• {rec}\n"
            else:
                text = "✅ Товар не вызывает подозрений"

            await message.answer(text, parse_mode="HTML")
        else:
            await message.answer("⚠️ Формат: Название, Цена\nПример: Спиннинг Shimano, 5000")

        verify_states[user_id] = {}


@router.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    from bot.keyboards import main_menu_kb
    await callback.message.edit_text(
        "🎣 Главное меню\n\nВыберите действие:",
        reply_markup=main_menu_kb()
    )