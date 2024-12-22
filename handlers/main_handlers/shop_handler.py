from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.shop_keyboards import get_shop_main_keyboard

router = Router()

@router.callback_query(F.data == "shop")
async def show_shop_menu(callback: CallbackQuery):
    try:
        await callback.message.bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id + 1	
        )
    except:
        print("delete_message error in show_shop_menu")
        pass

    await callback.message.edit_text(
        text="✨ Всё что мы можем предложить на сегодняшний день ✨",
        reply_markup=get_shop_main_keyboard()
    )
