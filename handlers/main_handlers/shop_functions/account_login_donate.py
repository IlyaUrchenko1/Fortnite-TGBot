from aiogram import F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from utils.database import Database
from keyboards.user_keyboards import to_home_menu_inline
from handlers.main_handlers.shop_functions.code_donate import get_admin_confirm_keyboard_login
from utils.varibles import COURSE_V_BAKS_TO_RUBLE
router = Router()
db = Database()

ADMIN_GROUP_CHAT_ID = -1002389059389

# Состояния для кастомного доната
class CustomDonateStates(StatesGroup):
    entering_amount = State()
    confirming = State()
    entering_credentials = State()
    admin_confirmation = State()

def get_custom_donate_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="custom_confirm_donate")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="custom_cancel_donate")]
        ]
    )

def calculate_price(vbucks: int) -> float:
    """Рассчитывает цену в рублях на основе количества в-баксов"""
    base_rate = COURSE_V_BAKS_TO_RUBLE  # Базовый курс: 1 в-бакс = 0.95 рубля
    return round(vbucks * base_rate, 2)

@router.callback_query(F.data == "shop_account_donate")
async def custom_donate_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "💰 Введите желаемое количество в-баксов (минимум 50):\n\n"
        f"Текущий курс: 1 в-бакс = {COURSE_V_BAKS_TO_RUBLE}₽"

    )
    await state.set_state(CustomDonateStates.entering_amount)

@router.message(CustomDonateStates.entering_amount)
async def process_custom_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
        if amount < 50:
            await message.answer(
                "❌ Минимальная сумма доната - 50 в-баксов\n"
                "Пожалуйста, введите сумму больше или равную 50"
            )
            return
            
        price = calculate_price(amount)
        await state.update_data(amount=amount, price=price)
        
        await message.answer(
            f"🎉 Вы хотите приобрести {amount} в-баксов за {price}₽\n\n"
            "Подтверждаете заказ?",
            reply_markup=get_custom_donate_keyboard()
        )
        await state.set_state(CustomDonateStates.confirming)
        
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите корректное число в-баксов\n"
            "Только цифры, без пробелов и других символов"
        )

@router.callback_query(F.data == "custom_cancel_donate")
async def custom_donate_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "❌ Донат отменен. Вы можете вернуться в главное меню.", 
        reply_markup=to_home_menu_inline()
    )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "custom_confirm_donate")
async def custom_donate_confirm(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🔑 Пожалуйста, введите ваш ник и пароль через пробел.\n\n"
        "Пример: NickName Password123"
    )
    await state.set_state(CustomDonateStates.entering_credentials)

@router.message(CustomDonateStates.entering_credentials)
async def custom_donate_credentials(message: Message, state: FSMContext):
    try:
        credentials = message.text.split()
        if len(credentials) < 2:
            await message.answer("❌ Пожалуйста, введите ник и пароль через пробел")
            return
            
        nickname = credentials[0]
        password = credentials[1]
        
        data = await state.get_data()
        amount = data.get("amount")
        price = data.get("price")
        user_id = message.from_user.id
        
        await message.delete()  # Удаляем сообщение с учетными данными
        
        await message.bot.send_message(
            ADMIN_GROUP_CHAT_ID,
            f"🔔 Новый кастомный донат!\n\n"
            f"Сумма: {amount} в-баксов\n"
            f"Цена: {price}₽\n"
            f"Ник: {nickname}\n"
            f"Пароль: {password}\n\n"
            f"User ID: {user_id}",
            reply_markup=get_admin_confirm_keyboard_login(user_id)
        )
        
        await message.answer(
            "✅ Ваши данные отправлены администратору.\n"
            "Ожидайте подтверждения.", 
            reply_markup=to_home_menu_inline()
        )
        await state.set_state(CustomDonateStates.admin_confirmation)
        
    except Exception as e:
        await message.answer(
            "❌ Произошла ошибка при обработке данных.\n"
            "Попробуйте еще раз или обратитесь в поддержку."
        )
        await state.clear()
