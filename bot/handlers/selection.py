from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards import back_to_menu_kb, selection_fish_kb, selection_type_kb
from bot.database import get_all_categories, get_gear_by_category, get_all_gear

router = Router()

recommendations = {
    "щука": ["Удочки", "Катушки", "Приманки"],
    "окунь": ["Удочки", "Катушки", "Приманки"],
    "карась": ["Удочки", "Лески", "Крючки"],
    "карп": ["Удочки", "Катушки", "Лески"],
    "судак": ["Удочки", "Катушки", "Приманки"],
    "форель": ["Удочки", "Катушки", "Приманки"],
}


@router.callback_query(lambda c: c.data == "selection")
async def selection_start(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎯 Подбор снастей для рыбалки\n\n"
        "Сначала выберите, какую рыбу хотите ловить:",
        reply_markup=selection_fish_kb()
    )


@router.callback_query(lambda c: c.data.startswith("fish_"))
async def select_fish(callback: CallbackQuery):
    fish = callback.data[5:]
    await callback.message.edit_text(
        f"🐟 {fish.capitalize()} — отличный выбор!\n\n"
        "Теперь выберите тип ловли:",
        reply_markup=selection_type_kb(fish)
    )


@router.callback_query(lambda c: c.data.startswith("type_"))
async def show_recommendations(callback: CallbackQuery):
    parts = callback.data.split("_")
    fishing_type = parts[1]
    fish = parts[2]

    rec_categories = recommendations.get(fish, get_all_categories())

    text = (
        f"🎣 Рекомендации для ловли {fish} ({fishing_type}):\n\n"
        "Рекомендуемые категории снастей:\n"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for cat in rec_categories:
        gear_list = get_gear_by_category(cat)
        if gear_list:
            keyboard.inline_keyboard.append(
                [InlineKeyboardButton(text=f"📦 {cat}", callback_data=f"cat_{cat}")]
            )

    if not rec_categories:
        gear_list = get_all_gear()
        for gear in gear_list[:5]:
            keyboard.inline_keyboard.append(
                [InlineKeyboardButton(text=f"🎣 {gear['name']}", callback_data=f"gear_{gear['id']}")]
            )

    keyboard.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="selection")])

    await callback.message.edit_text(text, reply_markup=keyboard)