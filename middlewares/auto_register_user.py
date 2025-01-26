from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from utils.database import Database

class AutoRegisterUserMiddleware(BaseMiddleware):
    def __init__(self):
        self.db = Database()

    async def __call__(self, handler, event, data):
        user_id = str(event.from_user.id)
        username = event.from_user.username or "Пользователь"

        # Проверяем, существует ли пользователь в базе данных
        if not self.db.is_exists(user_id):
            # Добавляем пользователя в базу данных
            self.db.add_user(user_id, username, None)

        # Продолжаем обработку события
        return await handler(event, data) 