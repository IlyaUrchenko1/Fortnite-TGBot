from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_shop_main_keyboard() -> InlineKeyboardBuilder:
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="🎁 Донат подарком", callback_data="shop_gift_donate"),
        InlineKeyboardButton(text="🔑 Донат через код", callback_data="shop_code_donate")
    )
    
    keyboard.row(
        InlineKeyboardButton(text="👤 Донат со входом", callback_data="shop_account_donate"),
        InlineKeyboardButton(text="⭐️ Боевой пропуск", callback_data="shop_battle_pass")
    )
    
    keyboard.row(InlineKeyboardButton(text="🗺 Купить Land Map", callback_data="shop_land_map"))

    keyboard.row(InlineKeyboardButton(text="➡ Присоедениься к ситсеме подарков", callback_data="shop_gift_join"))
    
    keyboard.row(InlineKeyboardButton(text="🏠 Вернуться в главное меню", callback_data="to_home_menu"))
    
    return keyboard.as_markup()

def get_back_to_shop_keyboard() -> InlineKeyboardBuilder:
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="◀️ Назад в магазин", callback_data="shop"))
    return keyboard.as_markup()
