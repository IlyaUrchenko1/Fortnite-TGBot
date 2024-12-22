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
            "• Удобный и быстрый процесс дарения\n"
            "• Доступ к эксклюзивным функциям\n\n"
            "📝 Чтобы присоединиться:\n"
            "1️⃣ Добавьте в друзья наших ботов:\n"
            "   • @Shop_bot10\n"
            "   • @Shop_bot20\n"
            "2️⃣ Готово! Теперь вы можете пользоваться всеми преимуществами системы\n\n"
            "🌟 Присоединяйтесь прямо сейчас и дарите подарки без ограничений!"
        ),
        reply_markup=get_back_to_shop_keyboard()
    )
