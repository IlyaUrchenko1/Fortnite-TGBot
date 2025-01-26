from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.database import Database
from utils.constants import GROUP_ID_SERVICE_PROVIDER, ADMIN_IDS
from keyboards.user_keyboards import to_home_menu_inline
from typing import List

router = Router()
db = Database()

class BPPurchaseStates(StatesGroup):
    waiting_for_email = State()
    waiting_for_comment = State()
    waiting_for_code = State()
    confirming = State()
    waiting_for_admin_photos = State()
    waiting_for_admin_comment = State()

BP_PRICES = {
    "regular": {"name": "Brawl Pass", "price": 820},
    "plus": {"name": "Brawl Pass Plus", "price": 1230}
}

def get_bp_brawl_keyboard():
    buttons = []
    for bp_type, info in BP_PRICES.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"{info['name']} - {info['price']}₽",
                callback_data=f"brawl_bp_buy_{bp_type}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="brawl_stars_back"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.callback_query(F.data == "brawl_stars_bp")
async def show_bp_brawl_menu(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            text=(
                "🎯 <b>Покупка Brawl Pass</b>\n\n"
                "📝 <b>Процесс покупки:</b>\n"
                "1. Выберите тип Brawl Pass\n"
                "2. Укажите почту от аккаунта\n"
                "3. Дождитесь подтверждения от администратора\n"
                "4. Введите код, который придет на почту\n"
                "5. Получите Brawl Pass и оставьте отзыв\n\n"
                "⚠️ <i>Важно: После оплаты дождитесь подтверждения от администратора</i>"
            ),
            reply_markup=get_bp_brawl_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        await callback.answer(f"❌ Произошла ошибка: {str(e)}", show_alert=True)

@router.callback_query(lambda c: c.data.startswith("brawl_bp_buy_"))
async def handle_bp_brawl_purchase(callback: CallbackQuery, state: FSMContext):
    try:
        bp_type = callback.data.split("_")[3]
        bp_info = BP_PRICES[bp_type]
        
        user = db.get_user(str(callback.from_user.id))
        if not user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return

        if user[3] < bp_info["price"]:
            await callback.answer("❌ Недостаточно средств на балансе", show_alert=True)
            return

        await state.update_data(
            bp_type=bp_info["name"],
            price=bp_info["price"],
            user_id=callback.from_user.id,
            username=callback.from_user.username or "Нет username"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data="brawl_bp_cancel")]
        ])

        await callback.message.edit_text(
            "📧 Пожалуйста, укажите почту от вашего аккаунта Brawl Stars:",
            reply_markup=keyboard
        )
        await state.set_state(BPPurchaseStates.waiting_for_email)
        await callback.answer()
        
    except Exception as e:
        await callback.answer(f"❌ Произошла ошибка: {str(e)}", show_alert=True)
        await state.clear()

@router.message(BPPurchaseStates.waiting_for_email)
async def process_email_brawl(message: Message, state: FSMContext):
    try:
        if not message.text or "@" not in message.text or "." not in message.text:
            await message.answer(
                "❌ Некорректный email. Пожалуйста, введите действительный email адрес.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="❌ Отменить", callback_data="brawl_bp_cancel")]
                ])
            )
            return
        
        await state.update_data(email=message.text.strip())
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏩ Пропустить", callback_data="brawl_bp_skip_comment")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="brawl_bp_cancel")]
        ])

        await message.answer(
            "💭 Пожалуйста, оставьте комментарий к заказу (или нажмите кнопку пропустить):",
            reply_markup=keyboard
        )
        await state.set_state(BPPurchaseStates.waiting_for_comment)
        
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
        await state.clear()

@router.callback_query(lambda c: c.data == "brawl_bp_skip_comment")
async def skip_comment_brawl(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        await process_order_brawl(callback.message, "нет", state)
    except Exception as e:
        await callback.message.answer(f"❌ Произошла ошибка: {str(e)}")
        await state.clear()

@router.message(BPPurchaseStates.waiting_for_comment)
async def process_comment_brawl(message: Message, state: FSMContext):
    try:
        await process_order_brawl(message, message.text, state)
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
        await state.clear()

async def process_order_brawl(message: Message, comment: str, state: FSMContext):
    try:
        data = await state.get_data()
        if not data:
            await message.answer("❌ Данные заказа не найдены. Начните покупку заново.")
            await state.clear()
            return
            
        # Снимаем деньги с баланса
        db.update_user(str(data["user_id"]), balance=-data["price"])
        
        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Отменить", callback_data=f"brawl_bp_admin_cancel_{data['user_id']}"),
                InlineKeyboardButton(text="👤 Профиль", url=f"tg://user?id={data['user_id']}")
            ],
            [
                InlineKeyboardButton(text="🔑 Запросить код", callback_data=f"brawl_bp_admin_request_code_{data['user_id']}"),
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"brawl_bp_admin_confirm_{data['user_id']}")
            ]
        ])

        await message.bot.send_message(
            chat_id=GROUP_ID_SERVICE_PROVIDER,
            text=(
                f"🛍 <b>Новый заказ Brawl Pass!</b>\n\n"
                f"👤 Покупатель: @{data['username']}\n"
                f"🎯 Тип: {data['bp_type']}\n"
                f"💰 Сумма: {data['price']}₽\n"
                f"📧 Почта: {data['email']}\n"
                f"💭 Комментарий: {comment}"
            ),
            reply_markup=admin_keyboard,
            parse_mode="HTML"
        )

        await message.answer(
            "✅ Заказ успешно создан!\n"
            "⏳ Ожидайте подтверждения от администратора",
            reply_markup=to_home_menu_inline()
        )
        
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
        if data and "price" in data and "user_id" in data:
            db.update_user(str(data["user_id"]), balance=data["price"])
        await state.clear()

@router.callback_query(lambda c: c.data.startswith("brawl_bp_admin_cancel_"))
async def handle_admin_cancel_brawl(callback: CallbackQuery):
    try:
        if callback.from_user.id not in ADMIN_IDS:
            await callback.answer("❌ У вас нет прав администратора", show_alert=True)
            return

        user_id = callback.data.split("_")[4]
        
        # Возвращаем деньги пользователю
        user_data = await callback.bot.get_state(user_id)
        if user_data and "price" in user_data:
            db.update_user(user_id, balance=user_data["price"])
        
        await callback.bot.send_message(
            chat_id=user_id,
            text="❌ Ваш заказ был отменен администратором",
            reply_markup=to_home_menu_inline()
        )
        
        await callback.message.edit_text(
            callback.message.text + "\n\n❌ Заказ отменен",
            reply_markup=None
        )
        
        await callback.answer("Заказ успешно отменен")
        
    except Exception as e:
        await callback.answer(f"❌ Произошла ошибка: {str(e)}", show_alert=True)

@router.callback_query(lambda c: c.data.startswith("brawl_bp_admin_request_code_"))
async def handle_admin_request_code_brawl(callback: CallbackQuery, state: FSMContext):
    try:
        if callback.from_user.id not in ADMIN_IDS:
            await callback.answer("❌ У вас нет прав администратора", show_alert=True)
            return

        user_id = int(callback.data.split("_")[5])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Ввести код", callback_data=f"brawl_bp_enter_code_{user_id}")]
        ])

        await callback.bot.send_message(
            chat_id=user_id,
            text="📤 Нажмите на кнопку ниже, чтобы ввести код, отправленный на почту",
            reply_markup=keyboard
        )
        
        await callback.answer("Запрос кода отправлен пользователю")
        
    except Exception as e:
        await callback.answer(f"❌ Произошла ошибка: {str(e)}", show_alert=True)

@router.callback_query(lambda c: c.data.startswith("brawl_bp_enter_code_"))
async def start_code_input_brawl(callback: CallbackQuery, state: FSMContext):
    try:
        user_id = int(callback.data.split("_")[4])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data="brawl_bp_cancel_code")]
        ])

        await state.set_state(BPPurchaseStates.waiting_for_code)
        await state.update_data(
            admin_message_id=callback.message.message_id,
            admin_chat_id=callback.message.chat.id,
            user_id=user_id,
            attempts=0
        )

        await callback.message.edit_text(
            "📤 Пожалуйста, введите код, отправленный на почту:\n\n"
            "⚠️ У вас есть 3 попытки для ввода правильного кода",
            reply_markup=keyboard
        )
        
    except Exception as e:
        await callback.answer(f"❌ Произошла ошибка: {str(e)}", show_alert=True)

@router.message(BPPurchaseStates.waiting_for_code)
async def process_code_brawl(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        
        if not data:
            await message.answer("❌ Ошибка: Данные не найдены")
            await state.clear()
            return
            
        if message.from_user.id != data.get("user_id"):
            return
            
        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Код неверный", callback_data=f"brawl_bp_wrong_code_{message.from_user.id}")
            ]
        ])

        await message.bot.send_message(
            chat_id=GROUP_ID_SERVICE_PROVIDER,
            text=(
                "🔑 Получен код от пользователя:\n"
                f"👤 Пользователь: @{message.from_user.username or 'Нет username'}\n"
                f"📝 Код: <code>{message.text}</code>"
            ),
            parse_mode="HTML",
            reply_markup=admin_keyboard
        )
            
        await message.answer(
            "✅ Код отправлен администраторам\n"
            "⏳ Ожидайте подтверждения"
        )
        
        await state.set_state(BPPurchaseStates.confirming)
        
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
        await state.clear()

@router.callback_query(lambda c: c.data.startswith("brawl_bp_wrong_code_"))
async def handle_wrong_code_brawl(callback: CallbackQuery, state: FSMContext):
    try:
        if callback.from_user.id not in ADMIN_IDS:
            await callback.answer("❌ У вас нет прав администратора", show_alert=True)
            return

        user_id = int(callback.data.split("_")[4])
        data = await state.get_data()
        attempts = data.get("attempts", 0) + 1
        
        if attempts >= 3:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Создать новый заказ", callback_data="brawl_stars_bp")]
            ])
            
            await callback.bot.send_message(
                chat_id=user_id,
                text=(
                    "❌ Превышено количество попыток ввода кода!\n"
                    "📧 Пожалуйста, создайте новый заказ с правильной почтой"
                ),
                reply_markup=keyboard
            )
            await state.clear()
            
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📝 Ввести код", callback_data=f"brawl_bp_enter_code_{user_id}")],
                [InlineKeyboardButton(text="❌ Отменить", callback_data="brawl_bp_cancel_code")]
            ])
            
            await callback.bot.send_message(
                chat_id=user_id,
                text=(
                    f"❌ Введенный код неверный! Осталось попыток: {3-attempts}\n"
                    "📤 Нажмите кнопку ниже, чтобы ввести код повторно"
                ),
                reply_markup=keyboard
            )
            
            await state.update_data(attempts=attempts)
        
        await callback.answer("Уведомление отправлено пользователю")
        
    except Exception as e:
        await callback.answer(f"❌ Произошла ошибка: {str(e)}", show_alert=True)

@router.callback_query(lambda c: c.data.startswith("brawl_bp_admin_confirm_"))
async def handle_admin_confirm_brawl(callback: CallbackQuery, state: FSMContext):
    try:
        if callback.from_user.id not in ADMIN_IDS:
            await callback.answer("❌ У вас нет прав администратора", show_alert=True)
            return

        user_id = int(callback.data.split("_")[4])
        await state.update_data(user_id=user_id, photos=[])
        await state.set_state(BPPurchaseStates.waiting_for_admin_photos)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Завершить загрузку фото", callback_data=f"brawl_bp_finish_photos_{user_id}")],
            [InlineKeyboardButton(text="❌ Пропустить фото", callback_data=f"brawl_bp_skip_photos_{user_id}")]
        ])
        
        await callback.message.answer(
            "📸 Загрузка фотографий для пользователя:\n\n"
            "1️⃣ Отправляйте фотографии по одной\n"
            "2️⃣ После каждой фотографии дождитесь подтверждения\n" 
            "3️⃣ Когда загрузите все фото, нажмите 'Завершить загрузку'\n\n"
            "⚠️ Важно: отправляйте фото по одному!",
            reply_markup=keyboard
        )
        await callback.answer()

    except Exception as e:
        await callback.answer(f"❌ Произошла ошибка: {str(e)}", show_alert=True)

@router.message(BPPurchaseStates.waiting_for_admin_photos, F.photo)
async def handle_admin_photos_brawl(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        photos = data.get("photos", [])
        photo_id = message.photo[-1].file_id
        photos.append(photo_id)
        await state.update_data(photos=photos)
        
        await message.answer(
            f"✅ Фото #{len(photos)} успешно загружено!\n"
            "📤 Можете отправить еще фото или нажать кнопку 'Завершить загрузку'"
        )
            
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

@router.callback_query(lambda c: c.data.startswith("brawl_bp_finish_photos_"))
async def finish_photos_brawl(callback: CallbackQuery, state: FSMContext):
    try:
        user_id = int(callback.data.split("_")[4])
        data = await state.get_data()
        photos = data.get("photos", [])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Пропустить комментарий", callback_data=f"brawl_bp_skip_comment_{user_id}")]
        ])

        photo_count = len(photos)
        await state.set_state(BPPurchaseStates.waiting_for_admin_comment)
        await callback.message.answer(
            f"📸 Загружено фотографий: {photo_count}\n"
            "💬 Теперь отправьте комментарий для пользователя:",
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        await callback.answer(f"❌ Произошла ошибка: {str(e)}", show_alert=True)

@router.callback_query(lambda c: c.data.startswith("brawl_bp_skip_photos_"))
async def skip_photos_brawl(callback: CallbackQuery, state: FSMContext):
    try:
        user_id = int(callback.data.split("_")[4])
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Пропустить комментарий", callback_data=f"brawl_bp_skip_comment_{user_id}")]
        ])
        
        await state.set_state(BPPurchaseStates.waiting_for_admin_comment)
        await callback.message.answer(
            "💬 Отправьте комментарий для пользователя:",
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        await callback.answer(f"❌ Произошла ошибка: {str(e)}", show_alert=True)

@router.message(BPPurchaseStates.waiting_for_admin_comment)
async def handle_admin_comment_and_finish_brawl(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        user_id = data.get("user_id")
        photos = data.get("photos", [])
        price = data.get("price", 0)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⭐️ Оставить отзыв", callback_data=f"brawl_bp_leave_review_{user_id}_{price}")],
            [InlineKeyboardButton(text="🏪 Вернуться в магазин", callback_data="shop")]
        ])

        completion_text = (
            "✅ Ваш заказ успешно выполнен!\n"
            "🎯 Brawl Pass активирован на вашем аккаунте\n\n"
            f"💬 Комментарий от администратора:\n{message.text}\n\n"
            "🌟 Пожалуйста, оставьте отзыв о покупке"
        )

        try:
            if photos:
                media = [InputMediaPhoto(media=photos[0], caption=completion_text)]
                media.extend([InputMediaPhoto(media=photo) for photo in photos[1:]])
                
                await message.bot.send_media_group(chat_id=user_id, media=media)
                await message.bot.send_message(
                    chat_id=user_id,
                    text="🔽 Используйте кнопки ниже:",
                    reply_markup=keyboard
                )
            else:
                await message.bot.send_message(
                    chat_id=user_id,
                    text=completion_text,
                    reply_markup=keyboard
                )
            
            await message.answer(
                "✅ Заказ успешно выполнен и отправлен пользователю"
            )
            
        except Exception as e:
            await message.answer(f"❌ Ошибка при отправке сообщения пользователю: {str(e)}")
            
        finally:
            await state.clear()
            
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
        await state.clear()

@router.callback_query(F.data == "brawl_bp_cancel_code")
async def cancel_code_brawl(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Вернуться в магазин", callback_data="shop")]
    ])
    
    await callback.message.edit_text(
        "❌ Ввод кода отменен",
        reply_markup=keyboard
    )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "brawl_bp_cancel")
async def cancel_purchase_brawl(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        if data and "user_id" in data and "price" in data:
            db.update_user(str(data["user_id"]), balance=data["price"])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Вернуться в магазин", callback_data="shop")]
        ])
        
        await callback.message.edit_text(
            "❌ Покупка отменена",
            reply_markup=keyboard
        )
        
        await state.clear()
        await callback.answer("Покупка отменена")
        
    except Exception as e:
        await callback.answer(f"❌ Произошла ошибка: {str(e)}", show_alert=True)
        await state.clear()
