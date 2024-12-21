from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from utils.database import Database

class CheckBanMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.db = Database()
        
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Get user ID based on event type
        if isinstance(event, Message):
            user_id = str(event.from_user.id)
            reply_method = event.answer
        else:
            user_id = str(event.from_user.id)
            reply_method = event.message.answer

        # Check if user is banned
        user = self.db.get_user(user_id)
        if user and user[6]:  # Check is_banned flag
            await reply_method(
                "❌ Вы заблокированы в боте.\n"
                "Для разблокировки обратитесь к главному админу @ar8am."
            )
            return
            
        return await handler(event, data)
