from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_profile_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="add_balance")],
        [InlineKeyboardButton(text="🎟 Использовать промокод", callback_data="use_promo")],
        [InlineKeyboardButton(text="🎁 Купить подарочный сертификат", callback_data="buy_certificate")],
        [InlineKeyboardButton(text="👥 Реферальная система", callback_data="referral_system")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
    ])

def get_back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
    ])