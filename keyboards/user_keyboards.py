from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def start_bot_menu() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    # Две строки по три кнопки
    keyboard.row(
        InlineKeyboardButton(text='🎁 Подарочные сертификаты', callback_data='gift_certificates'),
        InlineKeyboardButton(text='🛠 Поддержка', callback_data='support'),
        InlineKeyboardButton(text='📝 Отзывы', callback_data='reviews')
    )
    keyboard.row(
        InlineKeyboardButton(text='🔒 Гарантии', callback_data='guarantees'),
        InlineKeyboardButton(text='👤 Профиль', callback_data='profile')
    )

    # Одна большая кнопка снизу
    keyboard.add(InlineKeyboardButton(text='🛒 Магазин', callback_data='shop'))

    return keyboard.as_markup(resize_keyboard=True)


def to_home_menu() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardBuilder()

    keyboard.row(KeyboardButton(text='🏠 Вернуться назад'))  # Есть

    return keyboard.as_markup(resize_keyboard=True)
