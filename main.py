import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from middlewares.antiflood import AntiFloodMiddleware
from middlewares.private_chat import PrivateChatMiddleware
from middlewares.work_set import WorkSetMiddleware
from middlewares.check_ban import CheckBanMiddleware
from middlewares.auto_register_user import AutoRegisterUserMiddleware

from handlers import leave_reviews_handler, main_handler
from handlers.main_handlers import (
    info_reviews_handler,
    warranty_handler,
    support_handler,
    profile_handler,
    shop_handler,
)
from handlers.admin_handlers import (create_promocode_hendler, 
                                   ban_user_hendler,
                                   manage_balance,
                                   start_newsletter_hendler
                                   )
from handlers.main_handlers.shop_functions import (account_login_donate, land_map, 
                                                   gift_donate,
                                                   code_donate,
                                                   battle_pass,
                                                   gift_system_join
                                                   )
from handlers.main_handlers.shop_functions.BrawlStars import (
    get_bp_brawl_handler,
    gems_get_handler
)

load_dotenv()

default_setting = DefaultBotProperties(parse_mode='HTML')
bot = Bot(os.getenv("BOT_TOKEN"), default=default_setting)
dp = Dispatcher()

async def main():
    dp.message.middleware(AntiFloodMiddleware(limit=1)) 
    dp.message.middleware(PrivateChatMiddleware())
    # dp.message.middleware(WorkSetMiddleware())
    dp.message.middleware(CheckBanMiddleware())
    dp.message.middleware(AutoRegisterUserMiddleware())
    dp.callback_query.middleware(AutoRegisterUserMiddleware())

    dp.include_routers(
        main_handler.router,
        info_reviews_handler.router,
        leave_reviews_handler.router,
        warranty_handler.router,
        support_handler.router,
        profile_handler.router
    )

    dp.include_routers(
        create_promocode_hendler.router,
        ban_user_hendler.router,
        manage_balance.router,
        start_newsletter_hendler.router
    )

    dp.include_routers(
        shop_handler.router,
        land_map.router,
        battle_pass.router,
        code_donate.router,
        account_login_donate.router,
        gift_donate.router,
        gift_system_join.router
    )
    
    dp.include_routers(
        get_bp_brawl_handler.router,
        gems_get_handler.router
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
