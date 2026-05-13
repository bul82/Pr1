import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from bot.config import BOT_TOKEN
from bot.database import init_db

from bot.handlers import start, search, selection, used, verification

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Инициализация базы данных...")
    init_db()
    logger.info("База данных готова")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_routers(
        start.router,
        search.router,
        selection.router,
        used.router,
        verification.router,
    )

    logger.info("Бот запускается...")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())