from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.database import Database
import random
from datetime import datetime

from keyboards.profile_keyboards import get_profile_keyboard, get_back_keyboard
from utils.varibles import NICK_BOT


router = Router()
db = Database()


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    try:
        try:
            await callback.message.bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id + 1
            )
        except:
            print("delete_message error in show_profile")
            pass
            
        await callback.message.delete()
        
        user_data = db.get_user(str(callback.from_user.id))
        system_id = ''.join([str(random.randint(0, 9)) for _ in range(8)])
        
        profile_text = (
            f"👤 <b>Профиль пользователя</b>\n\n"
            f"🔢 ID в системе: #{system_id}\n"
            f"📱 Telegram ID: {callback.from_user.id}\n"
            f"💰 Баланс: {user_data[2]} V-Bucks\n"
            f"👥 Рефералов: {len(db.get_referrals(str(callback.from_user.id)))}\n\n"
            f"Выберите действие:"
        )
        
        await callback.message.answer(
            text=profile_text,
            reply_markup=get_profile_keyboard()
        )
        
    except Exception as e:
        await callback.message.answer(f"❌ Произошла ошибка: {str(e)}")

@router.callback_query(F.data == "add_balance")
async def add_balance(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "💰 Раздел пополнения баланса\n\nВ разработке...",
        reply_markup=get_back_keyboard()
    )

class PromoStates(StatesGroup):
    waiting_for_promo = State()

@router.callback_query(F.data == "use_promo")
async def use_promo(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "🎟 <b>Использование промокода</b>\n\n"
        "Введите промокод, который хотите активировать:",
        reply_markup=get_back_keyboard()
    )
    await state.set_state()

@router.message(PromoStates.waiting_for_promo)
async def process_promo(message: Message, state: FSMContext):
    if not message.text or not message.text.isalnum():
        return
    
    try:
        promo_code = message.text.upper()
        user_id = str(message.from_user.id)
        
        # Проверяем существование и валидность промокода
        promo_data = db.get_promocode(promo_code)
        
        if not promo_data:
            await message.answer(
                "❌ Такой промокод не существует!",
                reply_markup=get_back_keyboard()
            )
            await state.clear()
            return
            
        # Проверяем не истек ли срок действия
        if datetime.now() > datetime.strptime(promo_data[4], "%Y-%m-%d %H:%M:%S"):
            await message.answer(
                "❌ Срок действия промокода истек!",
                reply_markup=get_back_keyboard()
            )
            await state.clear()
            return
            
        # Проверяем количество использований
        if promo_data[3] <= 0:
            await message.answer(
                "❌ Промокод больше не действителен - закончились использования!",
                reply_markup=get_back_keyboard()
            )
            await state.clear()
            return
            
        # Проверяем не использовал ли пользователь этот промокод ранее
        if user_id in db.get_promo_users(promo_code):
            await message.answer(
                "❌ Вы уже использовали этот промокод!",
                reply_markup=get_back_keyboard()
            )
            await state.clear()
            return
            
        # Применяем промокод
        if promo_data[5]:  # Если это фиксированная сумма
            db.update_user(user_id, balance=promo_data[5])
            success_text = f"✅ Промокод успешно активирован!\n💰 На ваш баланс начислено {promo_data[5]} V-Bucks"
        else:  # Если это процент скидки
            db.update_user(user_id, amount_of_sale=promo_data[6])
            success_text = f"✅ Промокод успешно активирован!\n🎉 Вы получили скидку {promo_data[6]}%"
            
        # Обновляем количество использований промокода
        db.update_promocode(promo_code, amount_uses=1)
        # Записываем использование промокода пользователем
        db.update_promocode(promo_code, who_used_telegram_id=user_id)
        
        await message.answer(success_text, reply_markup=get_back_keyboard())
        await state.clear()
        
    except Exception as e:
        await message.answer(
            f"❌ Произошла ошибка при активации промокода: {str(e)}",
            reply_markup=get_back_keyboard()
        )
        await state.clear()

@router.message(PromoStates.waiting_for_promo)
async def invalid_promo(message: Message, state: FSMContext):
    await message.answer(
        "❌ Неверный формат промокода! Промокод может содержать только буквы и цифры.",
        reply_markup=get_back_keyboard()
    )

@router.callback_query(F.data == "buy_certificate")
async def buy_certificate(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "🎁 Покупка подарочного сертификата\n\nВ разработке...",
        reply_markup=get_back_keyboard()
    )

@router.callback_query(F.data == "referral_system")
async def referral_system(callback: CallbackQuery):
    await callback.message.delete()
    
    user_id = callback.from_user.id
    ref_link = f"https://t.me/{NICK_BOT}?start={user_id}"
    
    ref_text = (
        "👥 <b>Реферальная система</b>\n\n"
        "🎁 Приглашайте друзей и получайте бонусы!\n\n"
        "💎 За каждого приглашенного друга вы получите:\n"
        "💰 15 рублей на баланс\n\n"
        "📱 Ваша реферальная ссылка:\n"
        f"<code>{ref_link}</code>\n\n"
        "📢 Поделитесь ссылкой с друзьями и начните зарабатывать прямо сейчас!\n"
        "❗️ Бонус начисляется только за новых пользователей"
    )
    
    await callback.message.answer(
        text=ref_text,
        reply_markup=get_back_keyboard()
    )
