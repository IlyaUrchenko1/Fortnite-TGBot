from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.database import Database
import random
from datetime import datetime
import secrets

from keyboards.profile_keyboards import get_profile_keyboard, get_back_keyboard
from keyboards.user_keyboards import to_home_menu_inline
from utils.varibles import NICK_BOT, COURSE_V_BAKS_TO_RUBLE


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
            f"💰 Баланс: {user_data[3]}₽\n"
            f"👥 Рефералов: {len(db.get_referrals(str(callback.from_user.id)))}\n\n"
            f"Выберите действие:"
        )
        
        await callback.message.answer(
            text=profile_text,
            reply_markup=get_profile_keyboard()
        )
        
    except Exception as e:
        await callback.message.answer(f"❌ Произошла ошибка: {str(e)}")

class BalanceStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_payment = State()

@router.callback_query(F.data == "add_balance") 
async def add_balance(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "💰 <b>Пополнение баланса</b>\n\n"
        "💳 Введите сумму в рублях для пополнения:",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(BalanceStates.waiting_for_amount)

@router.message(BalanceStates.waiting_for_amount)
async def process_balance_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount < 100 or amount > 15000:
            raise ValueError
            
        await state.update_data(amount=amount)
        
        await message.answer(
            f"💎 Вы оплачиваете {amount}₽, и получаете на баланс {amount}₽ 🤩\n\n"
            "💳 Для оплаты переведите указанную сумму на карту:\n"
            "<code>2200 7006 3518 1125</code>\n\n"
            "📸 После оплаты отправьте скриншот чека",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(BalanceStates.waiting_for_payment)
        
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите корректную сумму от 100₽ до 15000₽",
            reply_markup=get_back_keyboard()
        )

@router.message(BalanceStates.waiting_for_payment)
async def process_payment_screenshot(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer(
            "❌ Пожалуйста, отправьте фото чека, только фото",
            reply_markup=get_back_keyboard()
        )
        return
    
    data = await state.get_data()
    
    await message.bot.send_photo(
        chat_id="-1002360777828",
        photo=message.photo[-1].file_id,
        caption=(
            "💰 <b>Новое пополнение баланса!</b>\n\n"
            f"👤 Пользователь: {message.from_user.full_name} (@{message.from_user.username})\n"
            f"💵 Сумма: {data['amount']}₽\n"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять", callback_data=f"approve_balance_{message.from_user.id}_{data['amount']}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_balance_{message.from_user.id}")
            ]
        ])
    )
    
    await message.answer(
        "✅ Ваша заявка отправлена на проверку!\n"
        "⏳ Ожидайте подтверждения оплаты",
        reply_markup=get_back_keyboard()
    )
    
    await state.clear()

@router.callback_query(F.data.startswith("approve_balance_"))
async def approve_balance_payment(callback: CallbackQuery):
    user_id = callback.data.split("_")[2]
    amount = int(callback.data.split("_")[3])
    
    db.update_user(user_id, balance=amount)
    
    await callback.bot.send_message(
        chat_id=user_id,
        text=(
            "✅ <b>Поздравляем! Ваш баланс успешно пополнен!</b>\n\n"
            f"💎 Начислено: {amount}₽"
        ),
        reply_markup=get_back_keyboard()
    )
    
    await callback.message.edit_reply_markup()
    await callback.answer("✅ Платеж подтвержден!")

@router.callback_query(F.data.startswith("reject_balance_"))
async def reject_balance_payment(callback: CallbackQuery):
    user_id = callback.data.split("_")[2]
    
    await callback.bot.send_message(
        chat_id=user_id,
        text=(
            "❌ К сожалению, ваша оплата не найдена или была отклонена\n"
            "💭 Если вы считаете, что произошла ошибка, обратитесь в поддержку"
        ),
        reply_markup=get_back_keyboard()
    )
    
    await callback.message.edit_reply_markup()
    await callback.answer("❌ Платеж отклонен")

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
    await state.set_state(PromoStates.waiting_for_promo)

@router.message(PromoStates.waiting_for_promo)
async def process_promo(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(
            "❌ Неверный формат промокода.",
            reply_markup=get_back_keyboard()
        )
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
        valid_until = datetime.strptime(promo_data[5], "%Y-%m-%d %H:%M:%S")  # Используем индекс 5 вместо 4
        if datetime.now() > valid_until:
            await message.answer(
                "❌ Срок действия промокода истек!",
                reply_markup=get_back_keyboard()
            )
            await state.clear()
            return
            
        # Проверяем количество использований
        current_uses = promo_data[4] if promo_data[4] else 0
        max_uses = promo_data[3]
        if max_uses and current_uses >= max_uses:
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
        amount_of_money = promo_data[7]
        amount_of_sale = promo_data[8]
        
        if amount_of_money:  # Если это фиксированная сумма
            db.update_user(user_id, balance=amount_of_money)
            success_text = f"✅ Промокод успешно активирован!\n💰 На ваш баланс начислено {amount_of_money} V-Bucks"
        elif amount_of_sale:  # Если это процент скидки
            db.update_user(user_id, amount_of_sale=amount_of_sale)
            success_text = f"✅ Промокод успешно активирован!\n🎉 Вы получили скидку {amount_of_sale}% на следующую покупку"
            
        # Обновляем количество использований промокода
        db.update_promocode(promo_code, amount_uses=1)
        # Записываем использование промокода пользователем
        db.update_promocode(promo_code, who_used_telegram_id=user_id)
        
        await message.answer(success_text, reply_markup=get_back_keyboard())
        await state.clear()
        
    except Exception as e:
        await message.answer(
            f"❌ Произошла ошибка при активации промокода. Попробуйте позже или обратитесь в поддержку - {e}",
            reply_markup=get_back_keyboard()
        )
        await state.clear()

    

class GiftCertificateStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_payment = State()

@router.callback_query(F.data == "buy_certificate")
async def buy_certificate(callback: CallbackQuery, state: FSMContext):
	await callback.message.delete()
	await callback.message.answer(
		"🎁 <b>Покупка подарочного сертификата</b>\n\n"
		"💝 Выберите сумму сертификата (от 110₽ до 15000₽):\n\n"
		"💡 Введите сумму числом, например: 1000",
		reply_markup=get_back_keyboard()
	)
	await state.set_state(GiftCertificateStates.waiting_for_amount)

@router.message(GiftCertificateStates.waiting_for_amount)
async def process_certificate_amount(message: Message, state: FSMContext):
	try:
		amount = float(message.text)
		if amount < 110 or amount > 15000:
			raise ValueError
			
		v_bucks = int(amount / COURSE_V_BAKS_TO_RUBLE)
		
		# Генерируем уникальный промокод
		promo_code = f"GIFT_{secrets.token_hex(8).upper()}"
		
		# Сохраняем данные
		await state.update_data(amount=amount, v_bucks=v_bucks, promo_code=promo_code)
		
		preview_text = (
			"🎊 <b>Подарочный сертификат Fortnite</b> 🎊\n\n"
			"🎮 Поздравляем! Вы получили подарочный сертификат!\n\n"
			f"💰 Номинал: {v_bucks} V-Bucks\n"
			f"🎫 Промокод: <code>{promo_code}</code>\n\n"
			"📝 Как активировать:\n"
			"1️⃣ Перейдите в раздел «Профиль»\n"
			"2️⃣ Нажмите «Активировать промокод»\n"
			"3️⃣ Введите код сертификата\n\n"
			"💫 Желаем приятных покупок!\n"
			"🤝 С уважением, команда Fortnite Shop"
		)
		
		await message.answer(f"📜 Так будет выглядеть ваш подарочный сертификат:\n\n{preview_text}")
        
		await message.answer(f"💳 Для оплаты переведите {amount}₽ на карту:\n<code>2200 7006 3518 1125</code>\n\n📸 После оплаты отправьте скриншот чека")
		await state.set_state(GiftCertificateStates.waiting_for_payment)
		
	except ValueError:
		await message.answer(
			"❌ Пожалуйста, введите корректную сумму от 110₽ до 15000₽",
			reply_markup=get_back_keyboard()
		)

@router.message(GiftCertificateStates.waiting_for_payment)
async def process_payment(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer(
            "❌ Пожалуйста, отправьте фото чека, только фото",
            reply_markup=get_back_keyboard()
        )
        return

    data = await state.get_data()
    
    # Отправляем на модерацию
    await message.bot.send_photo(
        chat_id="-1002360777828",
        photo=message.photo[-1].file_id,
        caption=(
            "🔔 <b>Новая покупка сертификата!</b>\n\n"
            f"👤 Покупатель: {message.from_user.full_name} (@{message.from_user.username})\n"
            f"💰 Сумма: {data['amount']}₽ ({data['v_bucks']} V-Bucks)\n"
            f"🎫 Промокод: <code>{data['promo_code']}</code>"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять", callback_data=f"approve_cert_{message.from_user.id}_{data['v_bucks']}_{data['promo_code']}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_cert_{message.from_user.id}")
            ]
        ])
    )
    
    await message.answer(
        "✅ Ваша заявка отправлена на проверку!\n"
        "⏳ Ожидайте подтверждения оплаты",
        reply_markup=get_back_keyboard()
    )
    
    await state.clear()

@router.callback_query(F.data.startswith("approve_cert_"))
async def approve_certificate(callback: CallbackQuery):
	user_id = callback.data.split("_")[2]
	promo_code = f"{callback.data.split('_')[4]}_{callback.data.split('_')[5]}"
	v_bucks = callback.data.split("_")[3]
	
	# Создаем промокод в базе
	db.add_promocode(
		code=promo_code,
		creator_id=user_id,
		max_uses=1,
		valid_until="2099-12-31 00:00:00",
		amount_of_money=v_bucks,
		amount_of_sale=None
	)
	
	# Отправляем пользователю уведомление
	await callback.bot.send_message(
		chat_id=user_id,
		text="🎉 <b>Поздравляем! Ваша оплата подтверждена!</b>\n"
		"📨 Сертификат будет отправлен следующим сообщением",
        reply_markup=to_home_menu_inline()
	)
	
	await callback.bot.send_message(
		chat_id=user_id,
		text=(
			"🎊 <b>Подарочный сертификат Fortnite</b> 🎊\n\n"
			"🎮 Поздравляем! Вы получили подарочный сертификат!\n\n"
			f"💰 Номинал: {v_bucks} V-Bucks\n"
			f"🎫 Промокод: <code>{promo_code}</code>\n\n"
			"📝 Как активировать:\n"
			"1️⃣ Перейдите в раздел «Профиль»\n"
			"2️⃣ Нажмите «Активировать промокод»\n"
			"3️⃣ Введите код сертификата\n\n"
			"💫 Желаем приятных покупок!\n"
			"🤝 С уважением, команда Fortnite Shop"
		)
	)
	
	await callback.message.edit_reply_markup()
	await callback.answer("✅ Сертификат успешно выдан!")

@router.callback_query(F.data.startswith("reject_cert_"))
async def reject_certificate(callback: CallbackQuery):
	user_id = callback.data.split("_")[2]
	
	await callback.bot.send_message(
		chat_id=user_id,
		text="❌ К сожалению, ваша оплата не найдена или была отклонена.\n"
		"💭 Если вы считаете, что произошла ошибка, обратитесь в поддержку.",
		reply_markup=get_back_keyboard()
	)
	
	await callback.message.edit_reply_markup()
	await callback.answer("❌ Заявка отклонена")
    
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


