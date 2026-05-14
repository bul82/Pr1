from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.filters import Command
from bot.keyboards import back_to_menu_kb, categories_kb, gear_list_kb, prices_kb, analogues_kb, main_menu_kb
from bot.database import (
    get_gear_by_category, get_gear_by_id, search_gear, get_all_gear,
    get_prices_for_gear, get_cheapest_price, get_analogues, add_shop, update_shop_verification
)
import json

router = Router()


@router.callback_query(lambda c: c.data == "categories")
async def show_categories(callback: CallbackQuery):
    await callback.message.edit_text(
        "📦 Выберите категорию:",
        reply_markup=categories_kb()
    )


@router.callback_query(lambda c: c.data.startswith("cat_"))
async def show_gear_in_category(callback: CallbackQuery):
    category = callback.data[4:]
    gear_list = get_gear_by_category(category)

    text = f"📦 {category}\n\nВыберите товар:"
    await callback.message.edit_text(
        text,
        reply_markup=gear_list_kb(gear_list, "gear")
    )


@router.callback_query(lambda c: c.data.startswith("gear_"))
async def show_gear_details(callback: CallbackQuery):
    gear_id = int(callback.data[5:])
    gear = get_gear_by_id(gear_id)

    if not gear:
        await callback.message.edit_text("Товар не найден.", reply_markup=back_to_menu_kb())
        return

    chars = json.loads(gear["characteristics"]) if gear["characteristics"] else {}
    chars_text = "\n".join([f"  {k}: {v}" for k, v in chars.items()])

    prices = get_prices_for_gear(gear_id)
    analogues = get_analogues(gear_id)

    text = (
        f"🎣 <b>{gear['name']}</b>\n\n"
        f"📝 {gear['description']}\n\n"
        f"📊 Характеристики:\n{chars_text}\n\n"
        f"💰 Цены в магазинах: {len(prices)} предложений"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    if prices:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="💰 Показать цены", callback_data=f"prices_{gear_id}")])

    if analogues:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔄 Аналоги", callback_data=f"analogues_{gear_id}")])

    keyboard.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(lambda c: c.data.startswith("prices_"))
async def show_prices(callback: CallbackQuery):
    gear_id = int(callback.data[7:])
    prices = get_prices_for_gear(gear_id)

    if not prices:
        await callback.message.edit_text("Нет данных о ценах.", reply_markup=back_to_menu_kb())
        return

    text = "💰 Цены в магазинах:\n\n"
    for p in prices:
        verified_icon = "✅" if p["shop_verified"] else "⚠️"
        text += f"{verified_icon} <b>{p['shop_name']}</b>: {p['price']}₽\n"

    await callback.message.edit_text(text, reply_markup=prices_kb(prices), parse_mode="HTML")


@router.callback_query(lambda c: c.data.startswith("analogues_"))
async def show_analogues(callback: CallbackQuery):
    gear_id = int(callback.data[10:])
    analogues = get_analogues(gear_id)

    if not analogues:
        await callback.message.edit_text("Аналоги не найдены.", reply_markup=back_to_menu_kb())
        return

    text = "🔄 Аналоги этого товара:\n\n"
    await callback.message.edit_text(text, reply_markup=analogues_kb(analogues), parse_mode="HTML")


@router.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎣 Главное меню\n\nВыберите действие:",
        reply_markup=main_menu_kb()
    )


@router.callback_query(lambda c: c.data == "all_gear")
async def show_all_gear(callback: CallbackQuery):
    gear_list = get_all_gear()

    if not gear_list:
        await callback.message.edit_text("Товары не найдены.", reply_markup=back_to_menu_kb())
        return

    await callback.message.edit_text(
        "📋 Все товары:",
        reply_markup=gear_list_kb(gear_list, "gear")
    )


@router.message(Command("search"))
async def cmd_search(message: Message):
    search_states[message.from_user.id] = {"waiting": True}
    await message.answer("🔍 Введите название товара:")


@router.callback_query(lambda c: c.data == "search")
async def search_callback(callback: CallbackQuery):
    search_states[callback.from_user.id] = {"waiting": True}
    await callback.message.edit_text("🔍 Введите название товара:")


search_states = {}


@router.message(F.text & ~F.text.startswith("/"))
async def handle_search(message: Message):
    user_id = message.from_user.id
    if user_id in search_states and search_states[user_id].get("waiting"):
        query = message.text.strip()
        if len(query) < 2:
            await message.answer("⚠️ Введите минимум 2 символа.")
            return

        results = search_gear(query)
        search_states[user_id]["waiting"] = False

        if results:
            text = f"🔍 Результаты по «{query}»:\n\n"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"{item['name']}", callback_data=f"gear_{item['id']}")]
                for item in results
            ])
            keyboard.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")])
            await message.answer(text, reply_markup=keyboard)
        else:
            await message.answer(f"😕 По «{query}» ничего не найдено.", reply_markup=back_to_menu_kb())