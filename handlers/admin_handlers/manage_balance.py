from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton

from utils.database import Database
from keyboards.user_keyboards import to_home_menu_inline
from utils.varibles import ADMIN_IDS

router = Router()
db = Database()

class ManageBalanceStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_action = State()
    waiting_for_amount = State()

def get_balance_action_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text='➕ Пополнить баланс', callback_data='add_balance'),
        InlineKeyboardButton(text='➖ Снять баланс', callback_data='subtract_balance')
    )
    return keyboard.as_markup()

@router.callback_query(F.data == "manage_balance_by_admin")
async def start_manage_balance(callback: CallbackQuery, state: FSMContext):
    if str(callback.from_user.id) not in ADMIN_IDS:
        await callback.message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    await callback.message.answer(
        "👤 Введите username пользователя (начиная с @):",
        reply_markup=to_home_menu_inline()
    )
    await state.set_state(ManageBalanceStates.waiting_for_username)

@router.message(ManageBalanceStates.waiting_for_username)
async def process_username(message: Message, state: FSMContext):
    if not message.text.startswith('@'):
        await message.answer(
            "❌ Username должен начинаться с @\nПопробуйте снова:",
            reply_markup=to_home_menu_inline()
        )
        return
    
    username = message.text[1:]  # Remove @ symbol
    user = db.get_user_by_username(username)
    
    if not user:
        await message.answer(
            "❌ Пользователь не найден.\nПопробуйте снова:",
            reply_markup=to_home_menu_inline()
        )
        return
    
    await state.update_data(user_id=user[1])  # Store user's telegram_id
    await message.answer(
        f"👤 Пользователь найден: {message.text}\n"
        f"💰 Текущий баланс: {user[4]} руб.\n\n"
        "Выберите действие:",
        reply_markup=get_balance_action_keyboard()
    )
    await state.set_state(ManageBalanceStates.waiting_for_action)

@router.callback_query(ManageBalanceStates.waiting_for_action, F.data.in_(['add_balance', 'subtract_balance']))
async def process_action(callback: CallbackQuery, state: FSMContext):
    action = "пополнения" if callback.data == "add_balance" else "снятия"
    await state.update_data(action=callback.data)
    
    await callback.message.answer(
        f"💰 Введите сумму для {action} баланса (в рублях):",
        reply_markup=to_home_menu_inline()
    )
    await state.set_state(ManageBalanceStates.waiting_for_amount)

@router.message(ManageBalanceStates.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите корректную сумму (положительное число):",
            reply_markup=to_home_menu_inline()
        )
        return
    
    data = await state.get_data()
    user_id = data['user_id']
    action = data['action']
    
    user = db.get_user(user_id)
    current_balance = float(user[4])
    
    if action == "add_balance":
        new_balance = current_balance + amount
        db.update_balance(user_id, new_balance)
        await message.answer(
            f"✅ Баланс пользователя успешно пополнен!\n\n"
            f"💰 Новый баланс: {new_balance} руб.",
            reply_markup=to_home_menu_inline()
        )
    else:
        if amount > current_balance:
            await message.answer(
                "❌ Недостаточно средств на балансе пользователя!",
                reply_markup=to_home_menu_inline()
            )
            await state.clear()
            return
            
        new_balance = current_balance - amount
        db.update_balance(user_id, new_balance)
        await message.answer(
            f"✅ Баланс пользователя успешно уменьшен!\n\n"
            f"💰 Новый баланс: {new_balance} руб.",
            reply_markup=to_home_menu_inline()
        )
    
    await state.clear()

@router.callback_query(F.data == "to_home_menu", ManageBalanceStates)
async def cancel_manage_balance(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "❌ Управление балансом отменено",
        reply_markup=to_home_menu_inline()
    )
    await state.clear()
