import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import setup_handlers
from middlewares import LoggingMiddleware
from logger import log
import database

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.message.middleware(LoggingMiddleware())
setup_handlers(dp)

async def on_startup():
    log.info("Запуск бота")
    await database.create_pool()
    log.info("Бот готов к работе")

async def on_shutdown():
    log.info("Остановка бота")
    await database.close_pool()
    log.info("Бот остановлен")

async def main():
    await on_startup()

    try:
        log.info("Бот запущен")
        await dp.start_polling(bot)
    finally:
        await on_shutdown()

if __name__ == "__main__":
    asyncio.run(main())
