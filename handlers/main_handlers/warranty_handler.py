from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.callback_query(F.data == "guarantees")
async def show_warranty_info(callback: CallbackQuery):
    try:
        try:
            await callback.message.bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id + 1
            )
        except:
            print("delete_message error in show_warranty_info")
            pass
            
        await callback.message.delete()
        
        warranty_text = (
            "🔐 <b>Гарантии безопасности</b>\n\n"
            "Мы дорожим каждым клиентом и гарантируем:\n"
            "✅ Безопасность ваших данных\n" 
            "✅ Качество предоставляемых услуг\n"
            "✅ Оперативную поддержку 24/7\n\n"
            "Ознакомьтесь с полными условиями гарантии, нажав на кнопку ниже 👇"
        )

        warranty_button = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="📋 Подробные условия гарантии",
                url="https://telegra.ph/Garantii-12-19-2"
            )],
            [InlineKeyboardButton(
                text="🏠 Вернуться в главное меню",
                callback_data="to_home_menu"
            )]
        ])

        await callback.message.answer(
            text=warranty_text,
            reply_markup=warranty_button
        )
        
    except Exception as e:
        error_message = f"❌ Произошла ошибка при показе гарантий: {str(e)}"
        await callback.message.answer(text=error_message)
