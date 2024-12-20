from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def start_bot_menu() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(InlineKeyboardButton(text='👤 Профиль', callback_data='profile'))
    keyboard.add(InlineKeyboardButton(text='📝 Отзывы', callback_data='reviews'))
    
    keyboard.row(InlineKeyboardButton(text='🛠 Поддержка', callback_data='support'))
    keyboard.add(InlineKeyboardButton(text='🔒 Гарантии', callback_data='guarantees'))
    
    keyboard.row(InlineKeyboardButton(text='🛒 Магазин', callback_data='shop'))

    return keyboard.as_markup()



def to_home_menu_reply() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardBuilder()

    keyboard.row(KeyboardButton(text='🏠 Вернуться в главное меню'))  # Есть

    return keyboard.as_markup(resize_keyboard=True)


def to_home_menu_inline() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text='🏠 Вернуться в главное меню', callback_data='to_home_menu'))

    return keyboard.as_markup()


def admin_menu() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text='🔖 Создать промокод', callback_data='create_promo_by_admin'))
    keyboard.row(InlineKeyboardButton(text='🚫 Бан пользователя', callback_data='ban_user_by_admin'))
    keyboard.row(InlineKeyboardButton(text='💲 Снять/Пополнить баланс', callback_data='manage_balance_by_admin'))

    return keyboard.as_markup(resize_keyboard=True)
