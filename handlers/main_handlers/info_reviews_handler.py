from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.callback_query(lambda cq: cq.data == "reviews")
async def get_rate_of_gold(callback: CallbackQuery):
    await callback.answer()
    
    reviews_text = (
        "Привет! 🌟\n\n"
        "Хотите узнать, что говорят о нас другие? Нажмите на кнопку ниже, "
        "чтобы прочитать отзывы наших клиентов! 📲✨\n\n"
        "Будем рады и вашему отзыву, который можно оставить после покупки, "
        "что мы вам и советуем делать! 💬❤️"
    )
    
    reviews_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📝 Посмотреть отзывы",
            url="https://t.me/arafortreviews"
        )]
    ])

    await callback.message.answer(
        text=reviews_text,
        reply_markup=reviews_button
    )