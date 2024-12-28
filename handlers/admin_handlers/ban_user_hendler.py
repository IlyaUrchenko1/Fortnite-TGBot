from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils.database import Database
from utils.constants import ADMIN_IDS
from keyboards.user_keyboards import admin_menu, back_to_admin_menu

router = Router()
db = Database()

# Состояния для FSM при бане пользователя
class BanUserStates(StatesGroup):
    waiting_for_username = State()

def get_banned_users_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру со списком забаненных пользователей
    и кнопками управления
    """
    keyboard = InlineKeyboardBuilder()
    
    # Получаем всех забаненных пользователей
    users = db.get_all_users()
    banned_users = [user for user in users if user[6]] # Проверяем флаг is_banned
    
    # Добавляем кнопки для каждого забаненного пользователя
    for user in banned_users:
        telegram_id = user[1]
        username = user[2] or "Без username" # Используем сохраненный username
        keyboard.row(InlineKeyboardButton(
            text=f"@{username}",
            callback_data=f"unban_{telegram_id}"
        ))
    
    # Добавляем кнопки управления
    keyboard.row(InlineKeyboardButton(
        text="🔒 Забанить пользователя", 
        callback_data="ban_new_user"
    ))
    
    keyboard.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_admin_menu"),
    )
    
    return keyboard.as_markup()

@router.callback_query(F.data == "ban_user_by_admin")
async def show_banned_users(callback: CallbackQuery):
    """Показывает список забаненных пользователей"""
    await callback.answer()
    await callback.message.delete()
    
    # Проверка прав администратора
    if callback.from_user.id not in ADMIN_IDS:
        await callback.message.answer("❌ У вас нет прав для использования этой команды!")
        return
        
    await callback.message.answer(
        "👥 <b>Список забаненных пользователей:</b>\n\n"
        "• Нажмите на пользователя для разбана\n"
        "• Нажмите «Забанить пользователя» для бана нового пользователя",
        reply_markup=get_banned_users_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "ban_new_user")
async def request_username(callback: CallbackQuery, state: FSMContext):
    """Запрашивает username пользователя для бана"""
    await callback.answer()
    await callback.message.edit_text(
        "👤 Введите username пользователя для бана\n"
        "❗️ Username должен начинаться с @",
        reply_markup=back_to_admin_menu()
    )
    await state.set_state(BanUserStates.waiting_for_username)

@router.message(BanUserStates.waiting_for_username)
async def ban_user(message: Message, state: FSMContext):
    """Обрабатывает бан пользователя по username"""
    if not message.text.startswith('@'):
        await message.answer(
            "❌ Username должен начинаться с @\n"
            "Попробуйте еще раз:",
            reply_markup=back_to_admin_menu()
        )
        return
    
    username = message.text[1:] # Убираем @
    user = db.get_user_by_username(username)
    
    if not user:
        await message.answer(
            "❌ Пользователь не найден\n"
            "Попробуйте еще раз:",
            reply_markup=back_to_admin_menu()
        )
        return

    # Проверяем, не забанен ли уже пользователь
    if user[6]:
        await message.answer(
            "❌ Этот пользователь уже забанен",
            reply_markup=back_to_admin_menu()
        )
        return
        
    # Баним пользователя
    db.update_user(user[1], is_banned=True)
    
    await message.answer(
        f"✅ Пользователь @{username} успешно заблокирован",
        reply_markup=get_banned_users_keyboard()
    )
    await state.clear()

@router.callback_query(F.data.startswith("unban_"))
async def unban_user(callback: CallbackQuery):
    """Обрабатывает разбан пользователя"""
    await callback.answer()
    
    telegram_id = callback.data.split("_")[1]
    user = db.get_user(telegram_id)
    
    if not user:
        await callback.message.edit_text(
            "❌ Пользователь не найден",
            reply_markup=get_banned_users_keyboard()
        )
        return
        
    # Разбаниваем пользователя
    db.update_user(telegram_id, is_banned=False)
    
    await callback.message.edit_text(
        f"✅ Пользователь @{user[2]} успешно разбанен",
        reply_markup=get_banned_users_keyboard()
    )