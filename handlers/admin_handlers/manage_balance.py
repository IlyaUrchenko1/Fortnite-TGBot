from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton

from utils.database import Database
from keyboards.user_keyboards import back_to_admin_menu, admin_menu
from utils.constants import ADMIN_IDS

router = Router()
db = Database()

# Состояния FSM для управления балансом
class ManageBalanceStates(StatesGroup):
    waiting_for_username = State()  # Ожидание ввода username
    waiting_for_action = State()    # Ожидание выбора действия
    waiting_for_amount = State()    # Ожидание ввода суммы

def get_balance_action_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с действиями для управления балансом"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text='➕ Пополнить баланс', callback_data='add_balance'),
        InlineKeyboardButton(text='➖ Снять баланс', callback_data='subtract_balance')
    )
    keyboard.row(
        InlineKeyboardButton(text='⬅️ Назад', callback_data='back_manage_balance'),
        InlineKeyboardButton(text='🏠 Главное меню', callback_data='to_home_menu')
    )
    return keyboard.as_markup()

@router.callback_query(F.data == "manage_balance_by_admin")
async def start_manage_balance(callback: CallbackQuery, state: FSMContext):
    """Начало процесса управления балансом"""
    await callback.answer()
    
    # Проверка прав администратора
    if callback.from_user.id not in ADMIN_IDS:
        await callback.message.answer("❌ У вас нет прав для выполнения этой команды!")
        return
    
    try:
        await callback.message.edit_text(
            "👤 Введите username пользователя (начиная с @):",
            reply_markup=back_to_admin_menu()
        )
        await state.set_state(ManageBalanceStates.waiting_for_username)
    except Exception as e:
        await callback.message.answer(f"❌ Произошла ошибка: {str(e)}")

@router.message(ManageBalanceStates.waiting_for_username)
async def process_username(message: Message, state: FSMContext):
    """Обработка введенного username"""
    if not message.text.startswith('@'):
        await message.answer(
            "❌ Username должен начинаться с @\nПопробуйте снова:",
            reply_markup=back_to_admin_menu()
        )
        return
    
    username = message.text[1:]  # Убираем символ @
    user = db.get_user_by_username(username)
    
    if not user:
        await message.answer(
            "❌ Пользователь не найден.\nПопробуйте снова:",
            reply_markup=back_to_admin_menu()
        )
        return
    
    # Сохраняем данные пользователя
    await state.update_data(user_id=user[1], username=username)
    
    await message.answer(
        f"👤 Пользователь найден: @{username}\n"
        f"💰 Текущий баланс: {user[4]} руб.\n\n"
        "Выберите действие:",
        reply_markup=get_balance_action_keyboard()
    )
    await state.set_state(ManageBalanceStates.waiting_for_action)

@router.callback_query(ManageBalanceStates.waiting_for_action, F.data.in_(['add_balance', 'subtract_balance']))
async def process_action(callback: CallbackQuery, state: FSMContext):
    """Обработка выбранного действия с балансом"""
    await callback.answer()
    
    action = "пополнения" if callback.data == "add_balance" else "снятия"
    await state.update_data(action=callback.data)
    
    try:
        await callback.message.edit_text(
            f"💰 Введите сумму для {action} баланса (в рублях):",
            reply_markup=back_to_admin_menu()
        )
        await state.set_state(ManageBalanceStates.waiting_for_amount)
    except Exception as e:
        await callback.message.answer(f"❌ Произошла ошибка: {str(e)}")

@router.message(ManageBalanceStates.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    """Обработка введенной суммы"""
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите корректную сумму (положительное число):",
            reply_markup=back_to_admin_menu()
        )
        return
    
    data = await state.get_data()
    user_id = data['user_id']
    username = data['username']
    action = data['action']
    
    user = db.get_user(user_id)
    if not user:
        await message.answer(
            "❌ Пользователь не найден в базе данных!",
            reply_markup=back_to_admin_menu()
        )
        await state.clear()
        return
        
    current_balance = float(user[4])
    
    try:
        if action == "add_balance":
            new_balance = current_balance + amount
            db.update_user(user_id=user_id, balance=amount)  # Используем amount как изменение
            await message.answer(
                f"✅ Баланс пользователя @{username} успешно пополнен!\n\n"
                f"💰 Было: {current_balance} руб.\n"
                f"💰 Стало: {new_balance} руб.\n"
                f"💰 Изменение: +{amount} руб.",
                reply_markup=back_to_admin_menu()
            )
        else:
            if amount > current_balance:
                await message.answer(
                    "❌ Недостаточно средств на балансе пользователя!",
                    reply_markup=back_to_admin_menu()
                )
                await state.clear()
                return
                
            new_balance = current_balance - amount
            db.update_user(user_id=user_id, balance=-amount)  # Используем -amount как изменение
            await message.answer(
                f"✅ Баланс пользователя @{username} успешно уменьшен!\n\n"
                f"💰 Было: {current_balance} руб.\n"
                f"💰 Стало: {new_balance} руб.\n"
                f"💰 Изменение: -{amount} руб.",
                reply_markup=back_to_admin_menu()
            )
    except Exception as e:
        await message.answer(
            f"❌ Произошла ошибка при обновлении баланса: {str(e)}",
            reply_markup=back_to_admin_menu()
        )
    
    await state.clear()

