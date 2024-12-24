from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from keyboards.shop_keyboards import get_back_to_shop_keyboard
from utils.database import Database
import re
import asyncio
from datetime import datetime, timedelta
from main import bot

router = Router()
db = Database()

# Dictionary to keep track of timers: user_id -> (end_time, nickname)
timers = {}

class GiftDonateStates(StatesGroup):
    waiting_for_donation_type = State()
    waiting_for_amount = State()
    waiting_for_nickname_regular = State()
    confirm_purchase_regular = State()
    waiting_for_confirmation_regular = State()
    waiting_for_join_confirmation = State()
    waiting_for_nickname_gift_system = State()
    confirm_purchase_gift_system = State()

@router.callback_query(F.data == "shop_gift_donate")
async def gift_donate_menu(callback: CallbackQuery, state: FSMContext):
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎁 Донат обычным подарком (48 часов ожидания)", callback_data="donate_regular_gift")],
            [InlineKeyboardButton(text="🎁 Донат через систему подарков (без ожидания)", callback_data="donate_gift_system_gift")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
        ])
        await callback.message.edit_text(
            "🎁 <b>Донат V-Bucks</b>\n\n"
            "💰 Курс: 100 V-Buck = 55₽\n"
            "💳 Минимальная сумма: 50₽\n\n"
            "Выберите способ доната:",
            reply_markup=keyboard
        )
        await state.set_state(GiftDonateStates.waiting_for_donation_type)
    except Exception as e:
        print(f"Error in gift_donate_menu: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже")

@router.callback_query(F.data == "donate_regular_gift", GiftDonateStates.waiting_for_donation_type)
async def donate_regular_gift(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_text(
            "🎁 <b>Донат обычным подарком</b>\n\n"
            "💰 Введите сумму в рублях (минимум 50₽):",
            reply_markup=get_back_to_shop_keyboard()
        )
        await state.set_state(GiftDonateStates.waiting_for_amount)
    except Exception as e:
        print(f"Error in donate_regular_gift: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже")

@router.message(GiftDonateStates.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
        if amount < 50:
            await message.answer(
                "❌ Минимальная сумма доната - 50₽",
                reply_markup=get_back_to_shop_keyboard()
            )
            return
            
        await state.update_data(amount=amount)
        await message.answer(
            "✏️ Введите ваш никнейм в Fortnite:\n\n"
            "ℹ️ Никнейм должен:\n"
            "• Содержать от 3 до 16 символов\n" 
            "• Состоять из букв, цифр и символов - _",
            reply_markup=get_back_to_shop_keyboard()
        )
        await state.set_state(GiftDonateStates.waiting_for_nickname_regular)
    except ValueError:
        await message.answer(
            "❌ Введите корректную сумму числом",
            reply_markup=get_back_to_shop_keyboard()
        )
    except Exception as e:
        print(f"Error in process_amount: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке суммы",
            reply_markup=get_back_to_shop_keyboard()
        )

@router.message(GiftDonateStates.waiting_for_nickname_regular)
async def process_nickname_regular(message: Message, state: FSMContext):
    try:
        if not 3 <= len(message.text) <= 16:
            await message.answer(
                "❌ Никнейм должен содержать от 3 до 16 символов",
                reply_markup=get_back_to_shop_keyboard()
            )
            return
                
        if not re.match("^[a-zA-Z0-9-_]+$", message.text):
            await message.answer(
                "❌ Никнейм может содержать только буквы, цифры и символы - _",
                reply_markup=get_back_to_shop_keyboard()
            )
            return

        user_data = await state.get_data()
        amount = user_data['amount']
        
        await state.update_data(nickname=message.text)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_gift_purchase_regular")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="to_home_menu")]
        ])
        
        await message.answer(
            f"📝 <b>Проверьте данные заказа:</b>\n\n"
            f"🎯 Никнейм: {message.text}\n"
            f"💰 Сумма: {amount}₽\n"
            f"💎 V-Bucks: {amount}\n\n"
            "Подтвердите заказ:",
            reply_markup=keyboard
        )
        await state.set_state(GiftDonateStates.confirm_purchase_regular)
    except Exception as e:
        print(f"Error in process_nickname_regular: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке никнейма",
            reply_markup=get_back_to_shop_keyboard()
        )

@router.callback_query(F.data == "confirm_gift_purchase_regular", GiftDonateStates.confirm_purchase_regular)
async def confirm_purchase_regular(callback: CallbackQuery, state: FSMContext):
    try:
        user_data = await state.get_data()
        amount = user_data['amount']
        user = db.get_user(telegram_id=callback.from_user.id)
        
        if not user:
            await callback.message.edit_text(
                "❌ Ошибка получения данных пользователя",
                reply_markup=get_back_to_shop_keyboard()
            )
            await state.clear()
            return

        try:
            balance = int(user[3])
        except ValueError:
            await callback.message.edit_text(
                "❌ Некорректные данные пользователя. Пожалуйста, свяжитесь с поддержкой.",
                reply_markup=get_back_to_shop_keyboard()
            )
            await state.clear()
            return

        if balance < amount:
            await callback.message.edit_text(
                f"❌ Недостаточно средств на балансе!\n\n"
                f"💰 Необходимо: {amount}₽\n"
                f"💳 Ваш баланс: {balance}₽\n\n"
                "📥 Пополните баланс для совершения покупки",
                reply_markup=get_back_to_shop_keyboard()
            )
            await state.clear()
            return

        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Выдано", callback_data=f"gift_sent_regular_{callback.from_user.id}_{user_data['nickname']}_{amount}"),
                InlineKeyboardButton(text="❌ Отмена", callback_data=f"gift_cancel_regular_{callback.from_user.id}")
            ],
            [InlineKeyboardButton(text="📱 Связаться", url=f"tg://user?id={callback.from_user.id}")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
        ])

        await callback.bot.send_message(
            chat_id="-1002389059389",
            text=(
                "🎁 <b>Новый заказ донат обычным подарком!</b>\n\n"
                f"👤 Покупатель: {callback.from_user.full_name}\n"
                f"🔗 Username: @{callback.from_user.username}\n"
                f"🆔 ID: <code>{callback.from_user.id}</code>\n"
                f"🎯 Никнейм: {user_data['nickname']}\n"
                f"💰 Сумма: {amount}₽"
            ),
            reply_markup=admin_keyboard
        )

        await callback.message.edit_text(
            "✅ Заявка успешно создана!\n\n"
            "⏳ Ожидайте подтверждения администратором.",
            reply_markup=get_back_to_shop_keyboard()
        )
        await state.set_state(GiftDonateStates.waiting_for_confirmation_regular)
    except Exception as e:
        print(f"Error in confirm_purchase_regular: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при создании заказа",
            reply_markup=get_back_to_shop_keyboard()
        )
        await state.clear()

@router.callback_query(F.data.startswith("gift_sent_regular_"))
async def gift_sent_regular(callback: CallbackQuery):
    try:
        parts = callback.data.split("_")
        user_id = int(parts[3])
        nickname_fortnite = parts[4]
        amount = int(parts[5])
        
        user = db.get_user(telegram_id=user_id)
        if not user:
            await callback.answer("❌ Пользователь не найден.")
            return

        nickname = user[2]

        # Записываем время окончания таймера
        end_time = datetime.now() + timedelta(hours=48)
        timers[user_id] = (end_time, nickname)

        # Списываем баланс
        db.update_user(str(user_id), balance=-amount)

        # Сообщение пользователю
        user_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏳ Проверить время", callback_data=f"check_time_regular_{user_id}")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
        ])
        
        await callback.bot.send_message(
            chat_id=user_id,
            text=(
                f"🎁 V-Bucks будут отправлены на ваш аккаунт по истечении 48 часов!\n\n"
                f"✅ Администрация подтвердила оплату.\n"
                f"⏳ Таймер на 48 часов запущен.\n"
                f"Осталось: 48:00:00 до выдачи вам подарка на ник : {nickname_fortnite}.\n\n"
            ),
            reply_markup=user_keyboard
        )
        
        # Сообщение администратору
        admin_keyboard_timer = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏳ Проверить оставшееся время", callback_data=f"check_time_regular_{user_id}")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
        ])
        
        await callback.bot.send_message(
            chat_id="-1002389059389",
            text=(
                f"✅ Донат обычным подарком для пользователя @{nickname} подтвержден.\n"
                "⏳ Таймер на 48 часов запущен.\n"
                f"Осталось: 48:00:00 до выдачи подарка пользователю на ник {nickname_fortnite}."
            ),
            reply_markup=admin_keyboard_timer
        )
        
        await callback.message.edit_reply_markup()
        await callback.answer("✅ Уведомления отправлены")
    
        # Запуск таймера на 48 часов
        asyncio.create_task(start_timer(user_id, 48))
    except Exception as e:
        print(f"Error in gift_sent_regular: {e}")
        await callback.answer("❌ Ошибка отправки уведомления")

async def start_timer(user_id: int, hours: int):
    try:
        await asyncio.sleep(hours * 3600)
        if user_id in timers:
            del timers[user_id]
        await bot.send_message(
            chat_id=user_id,
            text="⏰ Таймер на 48 часов истек. Ваш подарок должен быть доставлен."
        )
    except Exception as e:
        print(f"Error in start_timer: {e}")

# Система подарков (без ожидания)
@router.callback_query(F.data == "donate_gift_system_gift", GiftDonateStates.waiting_for_donation_type)
async def donate_gift_system(callback: CallbackQuery, state: FSMContext):
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, присоединился", callback_data="confirm_join_gift_system")],
            [InlineKeyboardButton(text="❌ Нет, вернуться", callback_data="to_home_menu")]
        ])
        await callback.message.edit_text(
            "🎁 <b>Донат через систему подарков</b>\n\n"
            "Вы уверены, что присоединились к системе подарков?",
            reply_markup=keyboard
        )
        await state.set_state(GiftDonateStates.waiting_for_join_confirmation)
    except Exception as e:
        print(f"Error in donate_gift_system: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже")

@router.callback_query(F.data == "confirm_join_gift_system", GiftDonateStates.waiting_for_join_confirmation)
async def confirm_join_gift_system(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_text(
            "💰 Введите сумму в рублях (минимум 50₽):",
            reply_markup=get_back_to_shop_keyboard()
        )
        await state.set_state(GiftDonateStates.waiting_for_amount)
    except Exception as e:
        print(f"Error in confirm_join_gift_system: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже")

@router.callback_query(F.data.startswith("check_time_"))
async def check_time(callback: CallbackQuery):
    try:
        parts = callback.data.split("_")
        user_id = int(parts[-1])

        if user_id not in timers:
            await callback.answer("⏳ Таймер не найден или уже истек.")
            return

        end_time, nickname = timers[user_id]
        now = datetime.now()
        remaining = end_time - now

        if remaining.total_seconds() <= 0:
            await callback.answer("⏳ Таймер истек.")
            del timers[user_id]
            return

        hours, remainder = divmod(int(remaining.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_left = f"{hours:02}:{minutes:02}:{seconds:02}"

        await callback.message.edit_text(
            f"⏳ Осталось: {time_left} до выдачи подарка.",
            reply_markup=get_back_to_shop_keyboard()
        )
        await callback.answer(f"⏳ Осталось: {time_left}")
    except Exception as e:
        print(f"Error in check_time: {e}")
        await callback.answer("❌ Ошибка при проверке времени")
