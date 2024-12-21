from aiogram import BaseMiddleware
from aiogram.types import Message
from utils.varibles import ADMIN_IDS

class WorkSetMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data):
        # Разрешаем админам команды отовсюду
        if event.from_user.id in ADMIN_IDS:
            return await handler(event, data)
        else:
            await event.answer("Cейчас бот находится в разработке. Просьба ожидать!")
            return
