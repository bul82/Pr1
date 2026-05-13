from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards import back_to_menu_kb, used_items_kb
from bot.database import get_used_items_for_gear, get_all_gear, search_gear, get_gear_by_id
from bot.parsers.base import parse_multiple_sources
import asyncio

router = Router()

used_search_states = {}


@router.callback_query(lambda c: c.data == "used_search")
async def used_search_start(callback: CallbackQuery):
    used_search_states[callback.from_user.id] = {"waiting_gear": True}
    gear_list = get_all_gear()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{gear['name']}", callback_data=f"used_gear_{gear['id']}")]
        for gear in gear_list[:10]
    ])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔍 Поиск по названию", callback_data="used_manual_search")])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")])

    await callback.message.edit_text(
        "🔎 Поиск б/у товаров\n\n"
        "Выберите товар или введите название:",
        reply_markup=keyboard
    )


@router.callback_query(lambda c: c.data == "used_manual_search")
async def used_manual_search(callback: CallbackQuery):
    used_search_states[callback.from_user.id] = {"waiting_name": True}
    await callback.message.edit_text("🔍 Введите название товара:")


@router.callback_query(lambda c: c.data.startswith("used_gear_"))
async def show_used_for_gear(callback: CallbackQuery):
    gear_id = int(callback.data[9:])
    items = get_used_items_for_gear(gear_id)

    if items:
        text = f"📍 Б/у товары ({len(items)}):\n\n"
        await callback.message.edit_text(text, reply_markup=used_items_kb(items))
    else:
        await callback.message.edit_text(
            "😕 Б/у товары не найдены.\n\n"
            "Хотите поискать на площадках вручную?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Искать на Avito", callback_data=f"used_parse_avito_{gear_id}")],
                [InlineKeyboardButton(text="🔍 Искать на OLX", callback_data=f"used_parse_olx_{gear_id}")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="used_search")]
            ])
        )


@router.callback_query(lambda c: c.data.startswith("used_parse_avito_"))
async def parse_avito(callback: CallbackQuery):
    gear_id = int(callback.data[14:])
    gear = get_gear_by_id(gear_id)

    await callback.message.edit_text(
        f"🔄 Ищу {gear['name']} на Avito...\n\n"
        "Это займёт некоторое время.",
        reply_markup=back_to_menu_kb()
    )

    search_url = f"https://www.avito.ru?q={gear['name']}+рыболовный"
    try:
        from bot.parsers.base import parse_product
        result = await parse_product("avito", search_url)

        if result.get("price"):
            await callback.message.answer(f"✅ Найдено на Avito: {result['price']}₽")
        else:
            await callback.message.answer("😕 На Avito ничего не найдено.")
    except Exception as e:
        await callback.message.answer(f"⚠️ Ошибка поиска: {e}")


@router.callback_query(lambda c: c.data.startswith("used_parse_olx_"))
async def parse_olx(callback: CallbackQuery):
    gear_id = int(callback.data[13:])
    gear = get_gear_by_id(gear_id)

    await callback.message.edit_text(
        f"🔄 Ищу {gear['name']} на OLX...\n\n"
        "Это займёт некоторое время.",
        reply_markup=back_to_menu_kb()
    )

    search_url = f"https://www.olx.ru/list/q-{gear['name']}-рыболовный"
    try:
        from bot.parsers.base import parse_product
        result = await parse_product("olx", search_url)

        if result.get("price"):
            await callback.message.answer(f"✅ Найдено на OLX: {result['price']}₽")
        else:
            await callback.message.answer("😕 На OLX ничего не найдено.")
    except Exception as e:
        await callback.message.answer(f"⚠️ Ошибка поиска: {e}")


@router.message(F.text & ~F.text.startswith("/"))
async def handle_used_search(message: Message):
    user_id = message.from_user.id
    state = used_search_states.get(user_id, {})

    if state.get("waiting_name"):
        query = message.text.strip()
        results = search_gear(query)

        if results:
            gear = results[0]
            items = get_used_items_for_gear(gear['id'])

            if items:
                text = f"📍 Б/у товары для «{gear['name']}»:\n\n"
                await message.answer(text, reply_markup=used_items_kb(items))
            else:
                await message.answer(
                    f"😕 Б/у для «{gear['name']}» не найдено в базе.\n\n"
                    "Хотите поискать на Avito?",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔍 Искать на Avito", callback_data=f"used_parse_avito_{gear['id']}")],
                        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
                    ])
                )
        else:
            await message.answer(f"😕 Товар «{query}» не найден.", reply_markup=back_to_menu_kb())

        used_search_states[user_id] = {}