from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.shop_keyboards import get_back_to_shop_keyboard

router = Router()

@router.callback_query(F.data == "shop_gift_join")
async def show_gift_system_info(callback: CallbackQuery):
    await callback.message.edit_text(
        text=(
            "🎁 <b>Система мгновенных подарков</b>\n\n"
            "✨ Хотите дарить подарки без ожидания? Присоединяйтесь к нашей системе мгновенных подарков!\n\n"
            "🔥 Преимущества:\n"
            "• Мгновенная отправка подарков без ожидания 48 часов\n"
            "• Удобное управление подарками через бот\n"
            "• Безопасные транзакции\n\n"
            "💡 Чтобы присоединиться, вам нужно добавить в друзья ники : Shop_bot10, Shop_bot20"
        ),
        reply_markup=get_back_to_shop_keyboard()
    )
