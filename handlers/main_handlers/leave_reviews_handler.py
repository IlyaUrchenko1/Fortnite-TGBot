import math
from datetime import date
from math import trunc

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.database import Database

router = Router()
db = Database()
chanel_id = -1002279802433  # Id канала для отправки отзывов


class LeaveReviewsStates(StatesGroup):
    waiting_many_star = State()
    waiting_text = State()


@router.callback_query(lambda cq: cq.data.startswith("leave_reviews_"))
async def start_reviews(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    data = await state.get_data()

    amount_gold = callback.data.split("_")[2]
    await state.update_data(amount_gold=amount_gold)
    await callback.message.answer("Выберите количество звезд", reply_markup=get_rating_keyboard())


@router.callback_query(lambda cq: cq.data.startswith("rating_"))
async def handle_rating(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    rating = int(callback.data.split("_")[1])
    await state.update_data(rating=rating)
    button = InlineKeyboardBuilder().add(
        InlineKeyboardButton(text="Отправить оценку без отзыва", callback_data="send_without_reviews")).as_markup()
    await callback.message.answer(f"Вы оценили нас на {'⭐️' * rating}", reply_markup=button)
    await callback.message.answer("Если хотите ввести текст отзыва, то напишите его снизу. Также можете приложить фото")
    await state.set_state(LeaveReviewsStates.waiting_text)


@router.callback_query(lambda cq: cq.data == "send_without_reviews")
async def post_only_text(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    if data.get("has_left_review", False) is True:
        await callback.message.answer("Вы уже оставляли отзыв и не можете сделать это снова.")
        return
    amount_gold = data.get("amount_gold")
    rating = data.get("rating")

    await callback.bot.send_message(
        chat_id=chanel_id,
        text=f"{'⭐️' * rating}\n\n"
             f"⬇️{callback.from_user.full_name}⬇️\n"
             f"Решил промолчать...\n\n"
             f"Вывел {amount_gold}В-Баксов, {date.today()}"
    )

    await state.update_data(has_left_review=True)

    link = "t.me/ARANEWSSHOPREVIEWS"
    await callback.message.answer(
        f"Вы успешно оставили отзыв! Вы можете его посмотреть в нашем телеграм канале с отзывами - {link}")


@router.message(LeaveReviewsStates.waiting_text)
async def process_text(message: Message, state: FSMContext):
    text_to_reviews = message.text
    data = await state.get_data()
    amount_gold = data.get("amount_gold")
    rating = data.get("rating")

    if data.get("has_left_review", False) is True:
        await message.answer("Вы уже оставляли отзыв и не можете сделать это снова.")
        return

    if message.photo:
        # Отправляем фото вместе с текстом отзыва
        photo = message.photo[-1]  # Получаем самое большое фото
        await message.bot.send_photo(
            chat_id=chanel_id,
            photo=photo.file_id,
            caption=f"{'⭐️' * rating}\n\n"
                    f"⬇️{message.from_user.full_name}⬇️\n"
                    f"{message.caption}\n\n"
                    f"Вывел {amount_gold}В-Баксов, {date.today()}"
        )
    else:
        # Если фото нет, просто отправляем текст
        await message.bot.send_message(
            chat_id=chanel_id,
            text=f"{'⭐️' * rating}\n\n"
                 f"⬇️{message.from_user.full_name}⬇️\n"
                 f"{message.text}\n\n"
                 f"Вывел {amount_gold}В-Баксов, {date.today()}"
        )

    await state.update_data(has_left_review=True)

    link = "t.me/ARANEWSSHOPREVIEWS"
    await message.answer(
        f"Вы успешно оставили отзыв! Вы можете его посмотреть в нашем телеграм канале с отзывами - {link}")


def get_rating_keyboard():
    keyboard = InlineKeyboardBuilder()
    for i in range(1, 6):
        keyboard.row(InlineKeyboardButton(text="⭐️" * i, callback_data=f"rating_{i}"))
    return keyboard.as_markup()
