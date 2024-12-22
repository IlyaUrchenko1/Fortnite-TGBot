from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from utils.database import Database
from utils.varibles import ADMIN_IDS
from keyboards.user_keyboards import to_home_menu_inline

router = Router()
db = Database()

class BanUserStates(StatesGroup):
    waiting_for_username = State()

def get_banned_users_keyboard() -> InlineKeyboardBuilder:
    keyboard = InlineKeyboardBuilder()
    
    users = db.get_all_users()
    banned_users = [user for user in users if user[5]] # Check is_banned flag
    
    for user in banned_users:
        user_id = user[1]  # telegram_id
        username = user[1] # Using telegram_id as display name since we don't store usernames
        keyboard.row(InlineKeyboardButton(
            text=f"{user_id} | {username}",
            callback_data=f"unban_{user_id}"
        ))
    
    keyboard.row(InlineKeyboardButton(
        text="🔒 Забанить пользователя", 
        callback_data="ban_new_user"
    ))
    
    keyboard.row(InlineKeyboardButton(
        text="🏠 Вернуться в меню",
        callback_data="to_home_menu"
    ))
    
    return keyboard

@router.callback_query(F.data == "ban_user_by_admin")
async def show_banned_users(callback: CallbackQuery):
    await callback.answer()
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.message.answer("❌ У вас нет прав для использования этой команды!")
        return
        
    await callback.message.answer(
        "👥 Список забаненных пользователей:\n"
        "Нажмите на кнопку с пользователем, чтобы разбанить его\n"
        "Или нажмите «Забанить пользователя» чтобы добавить нового",
        reply_markup=get_banned_users_keyboard().as_markup()
    )

@router.callback_query(F.data == "ban_new_user")
async def request_username(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Введите username пользователя, которого хотите забанить\n"
        "Username должен начинаться с @",
        reply_markup=to_home_menu_inline()
    )
    await state.set_state(BanUserStates.waiting_for_username)

@router.message(BanUserStates.waiting_for_username)
async def ban_user(message: Message, state: FSMContext):
    username = message.text
    
    if not username.startswith('@'):
        await message.answer(
            "❌ Username должен начинаться с @\n"
            "Попробуйте еще раз",
            reply_markup=to_home_menu_inline()
        )
        return
        
    # Remove @ from username
    telegram_username = username[1:]
    
    # Check if user exists
    if not db.is_exists_by_username(telegram_username):
        await message.answer(
            "❌ Пользователь не найден\n"
            "Попробуйте еще раз",
            reply_markup=to_home_menu_inline()
        )
        return
    
    user = db.get_user_by_username(telegram_username)
    # Ban user
    db.update_user(user[1], is_banned=True)
    
    await message.answer(
        f"✅ Пользователь {username} успешно забанен",
        reply_markup=get_banned_users_keyboard().as_markup()
    )
    await state.clear()

@router.callback_query(F.data.startswith("unban_"))
async def unban_user(callback: CallbackQuery):
    telegram_id = callback.data.split("_")[1]
    
    # Unban user
    db.update_user(telegram_id, is_banned=False)
    
    await callback.message.answer(
        f"✅ Пользователь успешно разбанен",
        reply_markup=get_banned_users_keyboard().as_markup()
    )

@router.callback_query(F.data == "to_home_menu", BanUserStates)
async def cancel_ban(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "❌ Операция отменена",
        reply_markup=to_home_menu_inline()
    )
    await state.clear()
