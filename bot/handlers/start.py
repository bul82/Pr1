from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from bot.keyboards import main_menu_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "🎣 Добро пожаловать в бот для подбора рыболовных снастей!\n\n"
        "Возможности бота:\n"
        "• Подбор снастей по виду рыбы и типу ловли\n"
        "• Сравнение цен в разных магазинах\n"
        "• Поиск б/у товаров с логистикой\n"
        "• Проверка надёжности магазинов\n"
        "• Анализ товаров и аналоги\n\n"
        "Выберите действие:",
        reply_markup=main_menu_kb()
    )