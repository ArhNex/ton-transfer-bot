import asyncio
import logging
from aiogram import Bot, Dispatcher
from app.handlers import router
from dotenv import load_dotenv
# from app.admin import admin
import os
from app.models import async_main


async def main():
    await async_main()
    bot = Bot(token=os.getenv('BOT_TOKEN'))
    dp = Dispatcher()
    dp.include_routers(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
