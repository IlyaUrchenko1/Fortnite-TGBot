import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from middlewares.antiflood import AntiFloodMiddleware
from middlewares.private_chat import PrivateChatMiddleware

from handlers import leave_reviews_handler, main_handler
from handlers.main_handlers import (
    info_reviews_handler,
    warranty_handler,
    support_handler,
    profile_handler,
    gift_certificate_handler,
    shop_handler,
)
from handlers.admin_handlers import create_promocode

load_dotenv()

default_setting = DefaultBotProperties(parse_mode='HTML')
bot = Bot(os.getenv("BOT_TOKEN"), default=default_setting)
dp = Dispatcher()

async def main():
    # dp.message.middleware(AntiFloodMiddleware(limit=1)) - антифлуд
    dp.message.middleware(PrivateChatMiddleware())
    
    dp.include_routers(
        main_handler.router,
        info_reviews_handler.router,
        leave_reviews_handler.router,
        warranty_handler.router,
        support_handler.router,
        profile_handler.router
    )
    
    dp.include_routers(
        create_promocode.router
    )

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()



if __name__ == '__main__':
    try:
        print("Бот стартовал :)")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен :(")
