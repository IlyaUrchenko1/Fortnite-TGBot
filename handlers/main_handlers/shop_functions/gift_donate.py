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

@router.callback_query(F.data == "gift_shop_donate")  # Changed from shop_gift_donate
async def gift_donate_menu(callback: CallbackQuery, state: FSMContext):
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎁 Донат обычным подарком (48 часов ожидания)", callback_data="gift_donate_regular")],  # Changed from donate_regular_gift
            [InlineKeyboardButton(text="🎁 Донат через систему подарков (без ожидания)", callback_data="gift_donate_system")],  # Changed from donate_gift_system_gift
            [InlineKeyboardButton(text="⏳ Проверить таймер", callback_data="check_gift_timer")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_shop")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]  # Changed from to_home_menu
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

@router.callback_query(F.data == "check_gift_timer")
async def check_gift_timer(callback: CallbackQuery):
    try:
        user_id = callback.from_user.id
        if user_id not in timers:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="gift_shop_donate")]
            ])
            await callback.message.edit_text(
                "❌ У вас нет активных таймеров на подарки",
                reply_markup=keyboard
            )
            return

        end_time, nickname = timers[user_id]
        now = datetime.now()
        remaining = end_time - now

        if remaining.total_seconds() <= 0:
            del timers[user_id]
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="gift_shop_donate")]
            ])
            await callback.message.edit_text(
                "✅ Таймер истек! Ваш подарок должен быть доставлен",
                reply_markup=keyboard
            )
            return

        hours, remainder = divmod(int(remaining.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_left = f"{hours:02}:{minutes:02}:{seconds:02}"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="check_gift_timer")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="gift_shop_donate")]
        ])

        await callback.message.edit_text(
            f"⏳ <b>Информация о вашем подарке:</b>\n\n"
            f"🎯 Никнейм: {nickname}\n"
            f"⌛️ Осталось времени: {time_left}\n\n"
            f"ℹ️ Подарок будет отправлен автоматически по истечении таймера",
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Error in check_gift_timer: {e}")
        await callback.answer("❌ Произошла ошибка при проверке таймера")

@router.callback_query(F.data == "gift_donate_regular", GiftDonateStates.waiting_for_donation_type)
async def donate_regular_gift(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_text(
            "🎁 <b>Донат обычным подарком</b>\n\n"
            "💰 Курс: 100 V-Buck = 55₽\n"
            "💳 Минимальная сумма: 50₽\n\n"
            "💰 Введите сумму в рублях :",
            reply_markup=get_back_to_shop_keyboard()
        )
        await state.set_state(GiftDonateStates.waiting_for_amount)
    except Exception as e:
        print(f"Error in donate_regular_gift: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже")

@router.message(GiftDonateStates.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        # Remove any non-digit characters
        amount = int(''.join(filter(str.isdigit, message.text)))
        
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
        nickname = message.text.strip()
        if not 3 <= len(nickname) <= 16:
            await message.answer(
                "❌ Никнейм должен содержать от 3 до 16 символов",
                reply_markup=get_back_to_shop_keyboard()
            )
            return
                
        if not re.match("^[a-zA-Z0-9-_]+$", nickname):
            await message.answer(
                "❌ Никнейм может содержать только буквы, цифр и символы - _",
                reply_markup=get_back_to_shop_keyboard()
            )
            return

        user_data = await state.get_data()
        amount = user_data['amount']
        vbucks = int(amount / 0.55)  # Convert rubles to V-Bucks based on rate
        
        await state.update_data(nickname=nickname, vbucks=vbucks)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="gift_confirm_purchase")],  # Changed callback
            [InlineKeyboardButton(text="❌ Отменить", callback_data="gift_cancel")]  # Changed callback
        ])
        
        await message.answer(
            f"📝 <b>Проверьте данные заказа:</b>\n\n"
            f"🎯 Никнейм: {nickname}\n"
            f"💰 Сумма: {amount}₽\n"
            f"💎 V-Bucks: {vbucks}\n\n"
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

@router.callback_query(F.data == "gift_confirm_purchase", GiftDonateStates.confirm_purchase_regular)
async def confirm_purchase_regular(callback: CallbackQuery, state: FSMContext):
    try:
        user_data = await state.get_data()
        amount = user_data['amount']
        nickname = user_data['nickname']
        vbucks = user_data['vbucks']
        
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
        except (ValueError, IndexError):
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
                InlineKeyboardButton(text="✅ Выдано", callback_data=f"gift_sent_{callback.from_user.id}_{nickname}_{amount}_{vbucks}"),
                InlineKeyboardButton(text="❌ Отмена", callback_data=f"gift_cancel_{callback.from_user.id}")
            ],
            [InlineKeyboardButton(text="📱 Связаться", url=f"tg://user?id={callback.from_user.id}")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="gift_admin_home")]
        ])

        await callback.bot.send_message(
            chat_id="-1002389059389",
            text=(
                "🎁 <b>Новый заказ донат обычным подарком!</b>\n\n"
                f"👤 Покупатель: {callback.from_user.full_name}\n"
                f"🔗 Username: @{callback.from_user.username}\n"
                f"🆔 ID: <code>{callback.from_user.id}</code>\n"
                f"🎯 Никнейм: {nickname}\n"
                f"💰 Сумма: {amount}₽\n"
                f"💎 V-Bucks: {vbucks}"
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

@router.callback_query(F.data.startswith("gift_sent_"))
async def gift_sent_regular(callback: CallbackQuery, state: FSMContext):
    try:
        parts = callback.data.split("_")
        user_id = int(parts[2])
        nickname_fortnite = parts[3]
        amount = int(parts[4])
        vbucks = int(parts[5])
        
        user = db.get_user(telegram_id=user_id)
        if not user:
            await callback.answer("❌ Пользователь не найден.")
            return

        nickname = user[2]

        # Списываем баланс
        db.update_user(str(user_id), balance=-amount)

        # Проверяем, является ли это обычным подарком или через систему подарков
        current_state = await state.get_state()
        if current_state == GiftDonateStates.waiting_for_confirmation_regular:
            # Для обычного подарка - запускаем таймер
            end_time = datetime.now() + timedelta(hours=48)
            timers[user_id] = (end_time, nickname)

            # Сообщение пользователю с таймером
            user_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⏳ Проверить время", callback_data=f"gift_check_time_{user_id}")],
                [InlineKeyboardButton(text="⭐️ Оставить отзыв", callback_data=f"leave_review_{user_id}_{amount}")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
            ])
            
            await callback.bot.send_message(
                chat_id=user_id,
                text=(
                    f"🎁 {vbucks} V-Bucks будут отправлены на ваш аккаунт по истечении 48 часов!\n\n"
                    f"✅ Администрация подтвердила оплату.\n"
                    f"⏳ Таймер на 48 часов запущен.\n"
                    f"Осталось: 48:00:00 до выдачи вам подарка на ник: {nickname_fortnite}.\n\n"
                ),
                reply_markup=user_keyboard
            )
            
            # Запуск таймера на 48 часов
            asyncio.create_task(start_timer(user_id, 48))
        else:
            # Для системы подарков - моментальная выдача
            user_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⭐️ Оставить отзыв", callback_data=f"leave_review_{user_id}_{amount}")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
            ])
            
            await callback.bot.send_message(
                chat_id=user_id,
                text=(
                    f"🎁 {vbucks} V-Bucks отправлены на ваш аккаунт!\n\n"
                    f"✅ Администрация подтвердила оплату.\n"
                    f"🎯 Никнейм получателя: {nickname_fortnite}\n\n"
                    "Спасибо за покупку!"
                ),
                reply_markup=user_keyboard
            )
        
        await callback.message.edit_reply_markup()
        await callback.answer("✅ Уведомления отправлены")
    
    except Exception as e:
        print(f"Error in gift_sent_regular: {e}")
        await callback.answer("❌ Ошибка отправки уведомления")

async def start_timer(user_id: int, hours: int):
    try:
        await asyncio.sleep(hours * 3600)
        if user_id in timers:
            end_time, nickname = timers[user_id]
            del timers[user_id]
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
            ])
            await bot.send_message(
                chat_id=user_id,
                text=f"⏰ Таймер на 48 часов истек. Ваш подарок для аккаунта {nickname} должен быть доставлен.",
                reply_markup=keyboard
            )
    except Exception as e:
        print(f"Error in start_timer: {e}")

@router.callback_query(F.data == "gift_donate_system", GiftDonateStates.waiting_for_donation_type)
async def donate_gift_system(callback: CallbackQuery, state: FSMContext):
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, присоединился", callback_data="gift_confirm_join")],
            [InlineKeyboardButton(text="❌ Нет, посмотреть условия", callback_data="shop_gift_join")]
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

@router.callback_query(F.data == "gift_confirm_join", GiftDonateStates.waiting_for_join_confirmation)
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

@router.callback_query(F.data.startswith("gift_check_time_"))
async def check_time(callback: CallbackQuery):
    try:
        user_id = int(callback.data.split("_")[-1])

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
            f"⏳ Осталось: {time_left} до выдачи подарка для аккаунта {nickname}.",
            reply_markup=get_back_to_shop_keyboard()
        )
        await callback.answer(f"⏳ Осталось: {time_left}")
    except Exception as e:
        print(f"Error in check_time: {e}")
        await callback.answer("❌ Ошибка при проверке времени")
