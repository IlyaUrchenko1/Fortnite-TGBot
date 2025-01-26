from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.database import Database
from utils.constants import GROUP_ID_SERVICE_PROVIDER, ADMIN_IDS
from keyboards.user_keyboards import to_home_menu_inline
from aiogram.types import InputMediaPhoto
import asyncio
from typing import List
router = Router()
db = Database()

class GemsPurchaseStates(StatesGroup):
    waiting_for_email = State()
    waiting_for_comment = State()
    waiting_for_code = State()
    confirming = State()
    waiting_for_admin_photos = State()
    waiting_for_admin_comment = State()

GEMS_PRICES = {
    "30": {"amount": "30+3", "price": 300},
    "80": {"amount": "80+8", "price": 700}, 
    "170": {"amount": "170+17", "price": 1250},
    "360": {"amount": "360+36", "price": 2550},
    "950": {"amount": "950+95", "price": 6000},
    "2000": {"amount": "2000+200", "price": 11500}
}

def get_gems_keyboard():
    buttons = []
    for amount in GEMS_PRICES.keys():
        buttons.append([
            InlineKeyboardButton(
                text=f"{GEMS_PRICES[amount]['amount']} гемов - {GEMS_PRICES[amount]['price']}₽",
                callback_data=f"buy_gems_{amount}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="brawl_stars"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.callback_query(F.data == "brawl_stars_gems")
async def show_gems_menu(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            text=(
                "💎 <b>Покупка гемов в Brawl Stars</b>\n\n"
                "📝 <b>Процесс покупки:</b>\n"
                "1. Выберите нужное количество гемов\n"
                "2. Укажите почту от аккаунта\n"
                "3. Дождитесь подтверждения от администратора\n"
                "4. Введите код, который придет на почту\n"
                "5. Получите гемы и оставьте отзыв\n\n"
                "⚠️ <i>Важно: После оплаты дождитесь подтверждения от администратора</i>"
            ),
            reply_markup=get_gems_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        await callback.answer(f"❌ Произошла ошибка: {str(e)}", show_alert=True)

@router.callback_query(lambda c: c.data.startswith("buy_gems_"))
async def handle_gems_purchase(callback: CallbackQuery, state: FSMContext):
    try:
        amount = callback.data.split("_")[2]
        gems_info = GEMS_PRICES[amount]
        
        user = db.get_user(str(callback.from_user.id))
        if not user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return

        if user[3] < gems_info["price"]:
            await callback.answer("❌ Недостаточно средств на балансе", show_alert=True)
            return

        await state.update_data(
            gems_amount=gems_info["amount"],
            price=gems_info["price"],
            user_id=callback.from_user.id,
            username=callback.from_user.username or "Нет username"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_purchase")]
        ])

        await callback.message.edit_text(
            "📧 Пожалуйста, укажите почту от вашего аккаунта Brawl Stars:",
            reply_markup=keyboard
        )
        await state.set_state(GemsPurchaseStates.waiting_for_email)
        
    except Exception as e:
        await callback.answer(f"❌ Произошла ошибка: {str(e)}", show_alert=True)
        await state.clear()

@router.message(GemsPurchaseStates.waiting_for_email)
async def process_email(message: Message, state: FSMContext):
    try:
        if not message.text or "@" not in message.text or "." not in message.text:
            await message.answer(
                "❌ Некорректный email. Пожалуйста, введите действительный email адрес.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_purchase")]
                ])
            )
            return
            
        await state.update_data(email=message.text.strip())
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏩ Пропустить", callback_data="skip_comment")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_purchase")]
        ])
        
        await message.answer(
            "💭 Пожалуйста, оставьте комментарий к заказу (или нажмите кнопку пропустить):",
            reply_markup=keyboard
        )
        await state.set_state(GemsPurchaseStates.waiting_for_comment)
        
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
        await state.clear()

@router.callback_query(lambda c: c.data == "skip_comment")
async def skip_comment(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        await process_order(callback.message, "нет", state)
    except Exception as e:
        await callback.message.answer(f"❌ Произошла ошибка: {str(e)}")
        await state.clear()

@router.message(GemsPurchaseStates.waiting_for_comment)
async def process_comment(message: Message, state: FSMContext):
    try:
        await process_order(message, message.text, state)
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
        await state.clear()

async def process_order(message: Message, comment: str, state: FSMContext):
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
                InlineKeyboardButton(text="❌ Отменить", callback_data=f"admin_cancel_{data['user_id']}"),
                InlineKeyboardButton(text="👤 Профиль", url=f"tg://user?id={data['user_id']}")
            ],
            [
                InlineKeyboardButton(text="🔑 Запросить код", callback_data=f"admin_request_code_{data['user_id']}")
            ]
        ])

        await message.bot.send_message(
            chat_id=GROUP_ID_SERVICE_PROVIDER,
            text=(
                f"🛍 <b>Новый заказ гемов!</b>\n\n"
                f"👤 Покупатель: @{data['username']}\n"
                f"💎 Количество: {data['gems_amount']}\n"
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

@router.callback_query(lambda c: c.data.startswith("admin_cancel_"))
async def handle_admin_cancel(callback: CallbackQuery):
    try:
        if callback.from_user.id not in ADMIN_IDS:
            await callback.answer("❌ У вас нет прав администратора", show_alert=True)
            return

        user_id = callback.data.split("_")[2]
        
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

@router.callback_query(lambda c: c.data.startswith("admin_request_code_"))
async def handle_admin_request_code(callback: CallbackQuery, state: FSMContext):
    try:
        if callback.from_user.id not in ADMIN_IDS:
            await callback.answer("❌ У вас нет прав администратора", show_alert=True)
            return

        user_id = int(callback.data.split("_")[3])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Ввести код", callback_data=f"enter_code_{user_id}")]
        ])

        await callback.bot.send_message(
            chat_id=user_id,
            text="📤 Нажмите на кнопку ниже, чтобы ввести код, отправленный на почту",
            reply_markup=keyboard
        )
        
        # Обновляем сообщение администратора
        await callback.message.edit_text(
            callback.message.text + "\n\n🔄 Ожидание кода от пользователя...",
            reply_markup=None
        )
        
        await callback.answer("Запрос кода отправлен пользователю")
        
    except Exception as e:
        await callback.answer(f"❌ Произошла ошибка: {str(e)}", show_alert=True)
        print(e)

@router.callback_query(lambda c: c.data.startswith("enter_code_"))
async def start_code_input(callback: CallbackQuery, state: FSMContext):
    try:
        user_id = int(callback.data.split("_")[2])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_code")]
        ])

        await state.set_state(GemsPurchaseStates.waiting_for_code)
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

@router.message(GemsPurchaseStates.waiting_for_code)
async def process_code(message: Message, state: FSMContext):
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
                InlineKeyboardButton(text="❌ Код неверный", callback_data=f"wrong_code_{message.from_user.id}"),
                InlineKeyboardButton(text="✅ Код верный", callback_data=f"gems_admin_confirm_{message.from_user.id}")
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
        
        await state.set_state(GemsPurchaseStates.confirming)
        
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
        await state.clear()

@router.callback_query(lambda c: c.data.startswith("wrong_code_"))
async def handle_wrong_code(callback: CallbackQuery, state: FSMContext):
    try:
        if callback.from_user.id not in ADMIN_IDS:
            await callback.answer("❌ У вас нет прав администратора", show_alert=True)
            return

        user_id = int(callback.data.split("_")[2])
        data = await state.get_data()
        attempts = data.get("attempts", 0) + 1
        
        if attempts >= 3:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Создать новый заказ", callback_data="brawl_stars_gems")]
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
                [InlineKeyboardButton(text="📝 Ввести код", callback_data=f"enter_code_{user_id}")],
                [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_code")]
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

@router.callback_query(lambda c: c.data.startswith("gems_admin_confirm_"))
async def handle_admin_confirm(callback: CallbackQuery, state: FSMContext):
    try:
        if callback.from_user.id not in ADMIN_IDS:
            await callback.answer("❌ У вас нет прав администратора", show_alert=True)
            return

        user_id = int(callback.data.split("_")[3])
        await state.update_data(user_id=user_id, photos=[])
        await state.set_state(GemsPurchaseStates.waiting_for_admin_photos)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Завершить загрузку фото", callback_data=f"finish_photos_{user_id}")],
            [InlineKeyboardButton(text="❌ Пропустить фото", callback_data=f"skip_photos_{user_id}")]
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

@router.message(GemsPurchaseStates.waiting_for_admin_photos, F.photo)
async def handle_admin_photo(message: Message, state: FSMContext):
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

@router.callback_query(lambda c: c.data.startswith("finish_photos_"))
async def finish_photos(callback: CallbackQuery, state: FSMContext):
    try:
        user_id = int(callback.data.split("_")[2])
        data = await state.get_data()
        photos = data.get("photos", [])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Пропустить комментарий", callback_data=f"skip_comment_{user_id}")]
        ])

        photo_count = len(photos)
        await state.set_state(GemsPurchaseStates.waiting_for_admin_comment)
        await callback.message.answer(
            f"📸 Загружено фотографий: {photo_count}\n"
            "💬 Теперь отправьте комментарий для пользователя:",
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        await callback.answer(f"❌ Произошла ошибка: {str(e)}", show_alert=True)

@router.callback_query(lambda c: c.data.startswith("skip_photos_"))
async def skip_photos(callback: CallbackQuery, state: FSMContext):
    try:
        user_id = int(callback.data.split("_")[2])
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Пропустить комментарий", callback_data=f"skip_comment_{user_id}")]
        ])
        
        await state.set_state(GemsPurchaseStates.waiting_for_admin_comment)
        await callback.message.answer(
            "💬 Отправьте комментарий для пользователя:",
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        await callback.answer(f"❌ Произошла ошибка: {str(e)}", show_alert=True)

@router.message(GemsPurchaseStates.waiting_for_admin_comment)
async def handle_admin_comment_and_finish(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        user_id = data.get("user_id")
        photos = data.get("photos", [])
        price = data.get("price", 0)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⭐️ Оставить отзыв", callback_data=f"leave_review_{user_id}_{price}")],
            [InlineKeyboardButton(text="🏪 Вернуться в магазин", callback_data="shop")]
        ])

        completion_text = (
            "✅ Ваш заказ успешно выполнен!\n"
            "💎 Гемы успешно зачислены на ваш аккаунт\n\n"
            f"💬 Сообщение от администратора:\n{message.text}\n\n"
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

@router.callback_query(F.data == "cancel_code")
async def cancel_code(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Вернуться в магазин", callback_data="shop")]
    ])
    
    await callback.message.edit_text(
        "❌ Ввод кода отменен",
        reply_markup=keyboard
    )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "cancel_purchase")
async def cancel_purchase(callback: CallbackQuery, state: FSMContext):
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
