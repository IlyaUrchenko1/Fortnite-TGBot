from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_fortnite_shop_main_keyboard() -> InlineKeyboardBuilder:
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="🎁 Донат подарком", callback_data="gift_shop_donate"),
        InlineKeyboardButton(text="🔑 Донат ключом", callback_data="shop_code_donate")
    )
    
    keyboard.row(
        InlineKeyboardButton(text="👤 Донат со входом", callback_data="shop_account_donate"),
        InlineKeyboardButton(text="⭐️ Боевой пропуск", callback_data="shop_battle_pass")
    )
    
    keyboard.row(InlineKeyboardButton(text="🗺 Купить Land Map", callback_data="shop_land_map"))
    
    keyboard.row(InlineKeyboardButton(text="➡ Присоединиться к системе подарков", callback_data="shop_gift_join"))
    
    keyboard.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")
    )
    
    return keyboard.as_markup()

def get_brawl_stars_shop_main_keyboard() -> InlineKeyboardBuilder:
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(InlineKeyboardButton(text="💎 Купить гемы", callback_data="brawl_stars_gems"))
    
    keyboard.row(InlineKeyboardButton(text="⭐️ Боевой пропуск", callback_data="brawl_stars_bp"))

    keyboard.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu"))
    
    return keyboard.as_markup()

def get_back_to_shop_keyboard() -> InlineKeyboardBuilder:
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text="◀️ Назад в магазин", callback_data="shop"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")
    )
    return keyboard.as_markup()