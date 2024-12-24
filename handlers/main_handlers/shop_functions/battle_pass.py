from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from keyboards.shop_keyboards import get_back_to_shop_keyboard
from utils.database import Database
import re
import asyncio
from datetime import datetime, timedelta
from bot import bot

router = Router()
db = Database()

# Dictionary to keep track of timers: user_id -> (end_time, nickname)
timers = {}

class BattlePassStates(StatesGroup):
    waiting_for_donation_type = State()
    waiting_for_nickname_regular = State()
    confirm_purchase_regular = State()
    waiting_for_confirmation_regular = State()
    waiting_for_join_confirmation = State()
    waiting_for_nickname_gift_system = State()
    confirm_purchase_gift_system = State()

@router.callback_query(F.data == "shop_battle_pass")
async def battle_pass_menu(callback: CallbackQuery, state: FSMContext):
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎁 Донат обычным подарком (48 часов ожидания)", callback_data="donate_regular_bp")],
            [InlineKeyboardButton(text="🎁 Донат через систему подарков (без ожидания)", callback_data="donate_gift_system_bp")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
        ])
        await callback.message.edit_text(
            "🎮 <b>Покупка Battle Pass</b>\n\n"
            "Выберите способ доната:",
            reply_markup=keyboard
        )
        await state.set_state(BattlePassStates.waiting_for_donation_type)
    except Exception as e:
        print(f"Error in battle_pass_menu: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже")

@router.callback_query(F.data == "donate_regular_bp", BattlePassStates.waiting_for_donation_type)
async def donate_regular_bp(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_text(
            "🎁 <b>Донат обычным подарком</b>\n\n"
            "✏️ Введите ваш никнейм в Fortnite:\n\n"
            "ℹ️ Никнейм должен:\n"
            "• Содержать от 3 до 16 символов\n" 
            "• Состоять из букв, цифр и символов - _",
            reply_markup=get_back_to_shop_keyboard()
        )
        await state.set_state(BattlePassStates.waiting_for_nickname_regular)
    except Exception as e:
        print(f"Error in donate_regular_bp: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже")

@router.message(BattlePassStates.waiting_for_nickname_regular)
async def process_nickname_regular(message: Message, state: FSMContext):
    try:
        # Проверка никнейма
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

        await state.update_data(nickname=message.text)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_bp_purchase_regular")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_bp_purchase_regular")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
        ])
        
        await message.answer(
            f"📝 <b>Проверьте данные заказа:</b>\n\n"
            f"👤 Никнейм: {message.text}\n"
            f"💰 Стоимость: 720₽\n\n"
            f"🎮 Battle Pass будет отправлен на ваш аккаунт по истечении 48 часов!\n\n"
            "❓ Подтверждаете покупку?",
            reply_markup=keyboard
        )
        await state.set_state(BattlePassStates.confirm_purchase_regular)
    except Exception as e:
        print(f"Error in process_nickname_regular: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке никнейма",
            reply_markup=get_back_to_shop_keyboard()
        )

@router.callback_query(F.data == "confirm_bp_purchase_regular", BattlePassStates.confirm_purchase_regular)
async def confirm_purchase_regular(callback: CallbackQuery, state: FSMContext):
    try:
        user_data = await state.get_data()
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

        if balance < 720:
            await callback.message.edit_text(
                f"❌ Недостаточно средств на балансе!\n\n"
                f"💰 Необходимо: 720₽\n"
                f"💳 Ваш баланс: {balance}₽\n\n"
                "📥 Пополните баланс для совершения покупки",
                reply_markup=get_back_to_shop_keyboard()
            )
            await state.clear()
            return

        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Выдано", callback_data=f"bp_gift_sent_regular_{callback.from_user.id}_{user_data['nickname']}"),
                InlineKeyboardButton(text="❌ Отмена", callback_data=f"bp_gift_cancel_regular_{callback.from_user.id}")
            ],
            [InlineKeyboardButton(text="📱 Связаться", url=f"tg://user?id={callback.from_user.id}")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
        ])

        await callback.bot.send_message(
            chat_id="-1002389059389",
            text=(
                "🎮 <b>Новый заказ донат обычным подарком : Battle Pass!</b>\n\n"
                f"👤 Покупатель: {callback.from_user.full_name}\n"
                f"🔗 Username: @{callback.from_user.username}\n"
                f"🆔 ID: <code>{callback.from_user.id}</code>\n"
                f"🎯 Никнейм: {user_data['nickname']}\n"
                f"💰 Сумма: 720₽"
            ),
            reply_markup=admin_keyboard
        )

        await callback.message.edit_text(
            "✅ Заявка успешно создана!\n\n"
            "⏳ Ожидайте подтверждения администратором.",
            reply_markup=get_back_to_shop_keyboard()
        )
        await state.set_state(BattlePassStates.waiting_for_confirmation_regular)
    except Exception as e:
        print(f"Error in confirm_purchase_regular: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при создании заказа",
            reply_markup=get_back_to_shop_keyboard()
        )
        await state.clear()

@router.callback_query(F.data.startswith("bp_gift_sent_regular_"))
async def gift_sent_regular(callback: CallbackQuery):
    try:
        user_id = int(callback.data.split("_")[4])
        nickname_fortnite = callback.data.split("_")[5]
        admin_id = callback.from_user.id
        
        user = db.get_user(telegram_id=user_id)
        if not user:
            await callback.answer("❌ Пользователь не найден.")
            return

        nickname = user[2]  # Предполагается, что никнейм находится на индексе 2

        # Записываем время окончания таймера
        end_time = datetime.now() + timedelta(hours=48)
        timers[user_id] = (end_time, nickname)

        # Сообщение пользователю
        user_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏳ Проверить время", callback_data=f"check_timer_regular_{user_id}")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
        ])
        
        await callback.bot.send_message(
            chat_id=user_id,
            text=(
                f"🎁 Battle Pass будет отправлен на ваш аккаунт по истечении 48 часов!\n\n"
                f"✅ Администрация подтвердила оплату.\n"
                f"⏳ Таймер на 48 часов запущен.\n"
                f"Осталось: 48:00:00 до выдачи вам подарка на ник : {nickname_fortnite}.\n\n"
            ),
            reply_markup=user_keyboard
        )
        
        # Сообщение администратору и владельцу
        admin_keyboard_timer = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏳ Проверить оставшееся время", callback_data=f"check_timer_regular_{user_id}")],
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
        # Логика окончания таймера, списание баланса и уведомление пользователя
        if user_id in timers:
            del timers[user_id]
        # Списываем баланс
        db.update_user(str(user_id), balance=-720)
        await bot.send_message(
            chat_id=user_id,
            text="⏰ Таймер на 48 часов истек. Ваш баланс был списан на 720₽."
        )
    except Exception as e:
        print(f"Error in start_timer: {e}")

@router.callback_query(F.data.startswith("check_timer_regular_"))
async def check_timer_regular(callback: CallbackQuery):
    try:
        user_id = int(callback.data.split("_")[3])
        
        if user_id not in timers:
            await callback.answer("⌛️ Таймер не найден или уже истек.")
            return

        end_time, nickname = timers[user_id]
        remaining_time = end_time - datetime.now()
        if remaining_time.total_seconds() < 0:
            await callback.answer("⏳ Таймер уже истек.")
            return

        hours, remainder = divmod(int(remaining_time.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        await callback.answer(f"⏳ Осталось времени: {time_str}")
    except Exception as e:
        print(f"Error in check_timer_regular: {e}")
        await callback.answer("❌ Ошибка при проверке таймера.")

@router.callback_query(F.data.startswith("bp_gift_cancel_regular_"))
async def cancel_purchase_regular(callback: CallbackQuery):
    try:
        user_id = int(callback.data.split("_")[4])
        
        await callback.bot.send_message(
            chat_id=user_id,
            text=(
                "❌ Ваша покупка Battle Pass отменена\n\n"
                "💭 Если есть вопросы - обратитесь в поддержку\n"
                "💰 Средства останутся на балансе"
            ),
            reply_markup=get_back_to_shop_keyboard()
        )
        
        await callback.message.edit_reply_markup()
        await callback.answer("❌ Покупка отменена")
    except Exception as e:
        print(f"Error in cancel_purchase_regular: {e}")
        await callback.answer("❌ Ошибка отмены покупки")





@router.callback_query(F.data == "donate_gift_system_bp", BattlePassStates.waiting_for_donation_type)
async def donate_gift_system_bp(callback: CallbackQuery, state: FSMContext):
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, присоединился", callback_data="confirm_join_gift_system_bp")],
            [InlineKeyboardButton(text="❌ Нет, вернуться", callback_data="to_home_menu")]
        ])
        await callback.message.edit_text(
            "🎁 <b>Донат через систему подарков</b>\n\n"
            "Вы уверены, что присоединились к системе подарков?",
            reply_markup=keyboard
        )
        await state.set_state(BattlePassStates.waiting_for_join_confirmation)
    except Exception as e:
        print(f"Error in donate_gift_system_bp: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже")

@router.callback_query(F.data == "confirm_join_gift_system_bp", BattlePassStates.waiting_for_join_confirmation)
async def confirm_join_gift_system_bp(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_text(
            "🎁 <b>Донат через систему подарков</b>\n\n"
            "✏️ Введите ваш никнейм в Fortnite:\n\n"
            "ℹ️ Никнейм должен:\n"
            "• Содержать от 3 до 16 символов\n" 
            "• Состоять из букв, цифр и символов - _",
            reply_markup=get_back_to_shop_keyboard()
        )
        await state.set_state(BattlePassStates.waiting_for_nickname_gift_system)
    except Exception as e:
        print(f"Error in confirm_join_gift_system_bp: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже")

@router.message(BattlePassStates.waiting_for_nickname_gift_system)
async def process_nickname_gift_system(message: Message, state: FSMContext):
    try:
        # Проверка никнейма
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

        await state.update_data(nickname_gift_system=message.text)
        
        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить зачисление", callback_data=f"confirm_gift_system_{message.from_user.id}"),
                InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_gift_system_{message.from_user.id}")
            ],
            [InlineKeyboardButton(text="📱 Связаться", url=f"tg://user?id={message.from_user.id}")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
        ])
        
        user_data = await state.get_data()
        await message.bot.send_message(
            chat_id="-1002389059389",
            text=(
                "🎁 <b>Новый донат через систему подарков!</b>\n\n"
                f"👤 Пользователь: {message.from_user.full_name}\n"
                f"🔗 Username: @{message.from_user.username}\n"
                f"🆔 ID: <code>{message.from_user.id}</code>\n"
                f"🎯 Никнейм: {user_data['nickname_gift_system']}"
            ),
            reply_markup=admin_keyboard
        )
        
        await message.answer(
            "✅ Ваш запрос отправлен администратору. Ожидайте подтверждения.",
            reply_markup=get_back_to_shop_keyboard()
        )
        await state.clear()
    except Exception as e:
        print(f"Error in process_nickname_gift_system: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке никнейма",
            reply_markup=get_back_to_shop_keyboard()
        )

@router.callback_query(F.data.startswith("confirm_gift_system_"))
async def confirm_gift_system(callback: CallbackQuery):
    try:
        user_id = int(callback.data.split("_")[3])
        
        user = db.get_user(telegram_id=user_id)
        if not user:
            await callback.answer("❌ Пользователь не найден.")
            return

        nickname = user[2]  # Assuming nickname is at index 2

        # Записываем время окончания таймера
        end_time = datetime.now() + timedelta(hours=48)
        timers[user_id] = (end_time, nickname)

        user_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Проверил, зачислено", callback_data=f"gift_system_confirmed_{user_id}")],
            [InlineKeyboardButton(text="❌ Не зачислено", callback_data=f"gift_system_not_confirmed_{user_id}")],
            [InlineKeyboardButton(text="⏳ Проверить оставшееся время", callback_data=f"check_time_gift_system_{user_id}")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
        ])
        
        await callback.bot.send_message(
            chat_id=user_id,
            text=(
                f"🎁 Ваш Battle Pass успешно зачислен на аккаунт!\n\n"
                "✅ Проверьте свой аккаунт. Если есть вопросы или проблемы, пожалуйста, обратитесь в поддержку.\n"
                "⏳ Таймер на 48 часов запущен.\n"
                f"Осталось: 48:00:00 до выдачи подарка пользователю на ник {nickname}."
            ),
            reply_markup=user_keyboard
        )
        
        # Сообщение администратору о запуске таймера
        admin_keyboard_timer = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏳ Проверить оставшееся время", callback_data=f"check_time_admin_gift_system_{user_id}")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
        ])
        
        await callback.bot.send_message(
            chat_id="-1002389059389",
            text=(
                f"✅ Донат через систему подарков для пользователя ID {user_id} подтвержден.\n"
                "⏳ Таймер на 48 часов запущен.\n"
                f"Осталось: 48:00:00 до выдачи подарка пользователю на ник {nickname}."
            ),
            reply_markup=admin_keyboard_timer
        )
        
        await callback.message.edit_reply_markup()
        await callback.answer("✅ Подарок зачислен пользователю и таймер запущен")
        
        # Запуск таймера на 48 часов
        asyncio.create_task(start_timer_gift_system(user_id, 48))
    except Exception as e:
        print(f"Error in confirm_gift_system: {e}")
        await callback.answer("❌ Ошибка подтверждения зачисления")

async def start_timer_gift_system(user_id: int, hours: int):
    try:
        await asyncio.sleep(hours * 3600)
        if user_id in timers:
            del timers[user_id]
        await bot.send_message(
            chat_id=user_id,
            text="⏰ Таймер на 48 часов истек. Если вы уже получили Battle Pass, пожалуйста, подтвердите получение."
        )
    except Exception as e:
        print(f"Error in start_timer_gift_system: {e}")

@router.callback_query(F.data.startswith("gift_system_confirmed_"))
async def gift_system_confirmed(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            "✅ Вы подтвердили зачисление Battle Pass.",
            reply_markup=get_back_to_shop_keyboard()
        )
    except Exception as e:
        print(f"Error in gift_system_confirmed: {e}")
        await callback.answer("❌ Ошибка подтверждения")

@router.callback_query(F.data.startswith("gift_system_not_confirmed_"))
async def gift_system_not_confirmed(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            "❌ Зачисление Battle Pass не подтверждено. Пожалуйста, обратитесь в поддержку.",
            reply_markup=get_back_to_shop_keyboard()
        )
    except Exception as e:
        print(f"Error in gift_system_not_confirmed: {e}")
        await callback.answer("❌ Ошибка подтверждения")

@router.callback_query(F.data.startswith("check_time_regular_") | F.data.startswith("check_time_gift_system_") | F.data.startswith("check_time_admin_regular_") | F.data.startswith("check_time_admin_gift_system_"))
async def check_time(callback: CallbackQuery):
    try:
        # Extract user_id from callback data
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
            f"⏳ Осталось: {time_left} до выдачи подарка пользователю на ник {nickname}.",
            reply_markup=get_back_to_shop_keyboard()
        )
        await callback.answer(f"⏳ Осталось: {time_left}")
    except Exception as e:
        print(f"Error in check_time: {e}")
        await callback.answer("❌ Ошибка при проверке времени")
