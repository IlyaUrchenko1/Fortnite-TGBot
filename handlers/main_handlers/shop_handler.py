from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.shop_keyboards import (
    get_fortnite_shop_main_keyboard,
    get_brawl_stars_shop_main_keyboard,
    get_back_to_shop_keyboard
)
from aiogram.fsm.context import FSMContext
from utils.constants import ADMIN_IDS
router = Router()

@router.callback_query(F.data == "shop")
async def show_shop_menu(callback: CallbackQuery):
    try:
        try:
            await callback.message.bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id + 1
            )
        except:
            pass

        games_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎮 Fortnite", callback_data="fortnite_shop")],
            [InlineKeyboardButton(text="⭐️ Brawl Stars", callback_data="brawl_stars")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
        ])
        
        await callback.message.edit_text(
            text="🎮 Выберите игру для покупки:",
            reply_markup=games_keyboard
        )
    except:
        print("delete_message error in show_shop_menu")
        pass

@router.callback_query(F.data == "fortnite_shop")
async def show_fortnite_shop(callback: CallbackQuery):
    await callback.message.edit_text(
        text="🎮 Магазин Fortnite\n\n"
             "Выберите интересующий вас товар:",
        reply_markup=get_fortnite_shop_main_keyboard()
    )

@router.callback_query(F.data == "brawl_stars")
async def show_brawl_stars_shop(callback: CallbackQuery):
    await callback.message.edit_text(
        text="⭐️ Магазин Brawl Stars\n\n"
             "Выберите интересующий вас товар:",
        reply_markup=get_brawl_stars_shop_main_keyboard()
    )
