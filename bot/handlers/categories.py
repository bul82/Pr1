from aiogram import Router
from aiogram.types import CallbackQuery
from bot.keyboards import categories_kb, gear_list_kb, back_to_menu_kb
from bot.database import get_gear_by_category, get_gear_by_id
import json

router = Router()


@router.callback_query(lambda c: c.data == "categories")
async def show_categories(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выберите категорию:",
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

    if gear:
        chars = json.loads(gear["characteristics"]) if gear["characteristics"] else {}
        chars_text = "\n".join([f"  {k}: {v}" for k, v in chars.items()])

        text = (
            f"🎣 <b>{gear['name']}</b>\n\n"
            f"📝 {gear['description']}\n\n"
            f"💰 Цена: <b>{gear['price']}₽</b>\n\n"
            f"📊 Характеристики:\n{chars_text}"
        )
        await callback.message.edit_text(
            text,
            reply_markup=back_to_menu_kb(),
            parse_mode="HTML"
        )


@router.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    from bot.keyboards import main_menu_kb
    await callback.message.edit_text(
        "🎣 Главное меню\n\nВыберите действие:",
        reply_markup=main_menu_kb()
    )