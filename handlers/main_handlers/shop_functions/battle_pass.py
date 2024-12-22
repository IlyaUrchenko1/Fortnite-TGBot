from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from keyboards.shop_keyboards import get_back_to_shop_keyboard
from utils.database import Database
import re

router = Router()
db = Database()

class BattlePassStates(StatesGroup):
    waiting_for_nickname = State()
    confirm_purchase = State()
    waiting_for_confirmation = State()

@router.callback_query(F.data == "shop_battle_pass")
async def battle_pass_gift_donate(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_text(
            "🎮 <b>Покупка Battle Pass подарком</b>\n\n"
            "✏️ Введите ваш никнейм в Fortnite:\n\n"
            "ℹ️ Никнейм должен:\n"
            "• Содержать от 3 до 16 символов\n" 
            "• Состоять из букв, цифр и символов - _",
            reply_markup=get_back_to_shop_keyboard()
        )
        await state.set_state(BattlePassStates.waiting_for_nickname)
    except Exception as e:
        print(f"Error in battle_pass_gift_donate: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже")

@router.message(BattlePassStates.waiting_for_nickname)
async def process_nickname(message: Message, state: FSMContext):
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
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_bp_purchase")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_bp_purchase")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
        ])
        
        await message.answer(
            f"📝 <b>Проверьте данные заказа:</b>\n\n"
            f"👤 Никнейм: {message.text}\n"
            f"💰 Стоимость: 720₽\n\n"
            "❓ Подтверждаете покупку?",
            reply_markup=keyboard
        )
        await state.set_state(BattlePassStates.confirm_purchase)
    except Exception as e:
        print(f"Error in process_nickname: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке никнейма",
            reply_markup=get_back_to_shop_keyboard()
        )

@router.callback_query(F.data == "confirm_bp_purchase", BattlePassStates.confirm_purchase)
async def confirm_purchase(callback: CallbackQuery, state: FSMContext):
    try:
        user_data = await state.get_data()
        user = db.get_user(str(callback.from_user.id))
        
        if not user:
            await callback.message.edit_text(
                "❌ Ошибка получения данных пользователя",
                reply_markup=get_back_to_shop_keyboard()
            )
            await state.clear()
            return

        if int(user[2]) < 720:
            await callback.message.edit_text(
                "❌ Недостаточно средств на балансе!\n\n"
                "💰 Необходимо: 720₽\n"
                "💳 Ваш баланс: {user[2]}₽\n\n"
                "📥 Пополните баланс для совершения покупки",
                reply_markup=get_back_to_shop_keyboard()
            )
            await state.clear()
            return

        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Выдано", callback_data=f"bp_gift_sent_{callback.from_user.id}"),
                InlineKeyboardButton(text="❌ Отмена", callback_data=f"bp_gift_cancel_{callback.from_user.id}")
            ],
            [InlineKeyboardButton(text="📱 Связаться", url=f"tg://user?id={callback.from_user.id}")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
        ])

        await callback.bot.send_message(
            chat_id="-1002389059389",
            text=(
                "🎮 <b>Новый заказ Battle Pass!</b>\n\n"
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
            "⏳ Ожидайте выдачи Battle Pass\n"
            "📱 Мы уведомим вас о получении",
            reply_markup=get_back_to_shop_keyboard()
        )
        await state.set_state(BattlePassStates.waiting_for_confirmation)
    except Exception as e:
        print(f"Error in confirm_purchase: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при создании заказа",
            reply_markup=get_back_to_shop_keyboard()
        )
        await state.clear()

@router.callback_query(F.data.startswith("bp_gift_sent_"))
async def gift_sent(callback: CallbackQuery):
    try:
        user_id = callback.data.split("_")[3]
        
        user_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Получил", callback_data=f"bp_confirm_received_{user_id}")],
            [InlineKeyboardButton(text="❌ Не получил", callback_data=f"bp_not_received_{user_id}")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
        ])
        
        await callback.bot.send_message(
            chat_id=user_id,
            text=(
                "🎁 Battle Pass отправлен на ваш аккаунт!\n\n"
                "✅ Пожалуйста, проверьте получение подарка\n"
                "❓ Подтвердите получение:"
            ),
            reply_markup=user_keyboard
        )
        
        await callback.message.edit_reply_markup()
        await callback.answer("✅ Уведомление отправлено")
    except Exception as e:
        print(f"Error in gift_sent: {e}")
        await callback.answer("❌ Ошибка отправки уведомления")

@router.callback_query(F.data.startswith("bp_confirm_received_"))
async def confirm_received(callback: CallbackQuery):
    try:
        user_id = callback.data.split("_")[3]
        
        # Списываем баланс
        db.update_user(str(callback.from_user.id), balance=-720)
        
        await callback.message.edit_text(
            "✅ Спасибо за подтверждение!\n\n"
            "💰 Списано: 720₽\n"
            "🎮 Приятной игры в Fortnite!",
            reply_markup=get_back_to_shop_keyboard()
        )
    except Exception as e:
        print(f"Error in confirm_received: {e}")
        await callback.message.edit_text(
            "❌ Ошибка подтверждения получения",
            reply_markup=get_back_to_shop_keyboard()
        )

@router.callback_query(F.data.startswith("bp_gift_cancel_"))
async def cancel_purchase(callback: CallbackQuery):
    try:
        user_id = callback.data.split("_")[3]
        
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
        print(f"Error in cancel_purchase: {e}")
        await callback.answer("❌ Ошибка отмены покупки")

@router.callback_query(F.data == "cancel_bp_purchase")
async def cancel_purchase_by_user(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_text(
            "❌ Покупка Battle Pass отменена\n"
            "💭 Вы можете сделать новый заказ в любое время",
            reply_markup=get_back_to_shop_keyboard()
        )
        await state.clear()
    except Exception as e:
        print(f"Error in cancel_purchase_by_user: {e}")
        await callback.answer("❌ Ошибка отмены")
        await state.clear()
