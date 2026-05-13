from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.database import get_all_categories

def main_menu_kb() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Категории", callback_data="categories")],
        [InlineKeyboardButton(text="🔍 Поиск", callback_data="search")],
        [InlineKeyboardButton(text="🎯 Подобрать снасти", callback_data="selection")],
        [InlineKeyboardButton(text="📋 Все товары", callback_data="all_gear")],
        [InlineKeyboardButton(text="🔎 Б/У товары", callback_data="used_search")],
        [InlineKeyboardButton(text="✅ Проверить магазин", callback_data="verify_shop")],
    ])
    return keyboard


def categories_kb() -> InlineKeyboardMarkup:
    categories = get_all_categories()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=cat, callback_data=f"cat_{cat}")]
        for cat in categories
    ])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")])
    return keyboard


def gear_list_kb(gear_list: list, prefix: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{item['name']} — {item.get('price', 'N/A')}₽", callback_data=f"{prefix}_{item['id']}")]
        for item in gear_list
    ])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")])
    return keyboard


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back_to_menu")]
    ])


def selection_fish_kb() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Щука", callback_data="fish_щука")],
        [InlineKeyboardButton(text="Окунь", callback_data="fish_окунь")],
        [InlineKeyboardButton(text="Карась", callback_data="fish_карась")],
        [InlineKeyboardButton(text="Карп", callback_data="fish_карп")],
        [InlineKeyboardButton(text="Судак", callback_data="fish_судак")],
        [InlineKeyboardButton(text="Форель", callback_data="fish_форель")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")],
    ])
    return keyboard


def selection_type_kb(fish: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Спиннинг", callback_data=f"type_спиннинг_{fish}")],
        [InlineKeyboardButton(text="Поплавок", callback_data=f"type_поплавок_{fish}")],
        [InlineKeyboardButton(text="Фидер", callback_data=f"type_фидер_{fish}")],
        [InlineKeyboardButton(text="Нахлыст", callback_data=f"type_нахлыст_{fish}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="selection")],
    ])
    return keyboard


def prices_kb(prices: list) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🏪 {p['shop_name']} — {p['price']}₽ ({'✅ проверен' if p['shop_verified'] else '⚠️'})",
            callback_data=f"price_{p['id']}"
        )]
        for p in prices
    ])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")])
    return keyboard


def used_items_kb(items: list) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"📍 {item['title']} — {item['price']}₽ ({item['condition']}) [{item['location']}]",
            callback_data=f"used_{item['id']}"
        )]
        for item in items
    ])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")])
    return keyboard


def analogues_kb(analogues: list) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🔄 {a['name']}", callback_data=f"gear_{a['id']}")]
        for a in analogues
    ])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")])
    return keyboard