from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards.user_keyboards import to_home_menu_inline
from keyboards.shop_keyboards import get_shop_main_keyboard
from utils.database import Database

router = Router()
db = Database()

# Constants
LAND_MAP_PRICE = 25
ADMIN_GROUP_ID = -1002389059389

class LandMapStates(StatesGroup):
    waiting_land_map_photos = State()

def get_land_map_keyboard() -> InlineKeyboardMarkup:
    """Generate keyboard for land map purchase screen"""
    keyboard = [
        [InlineKeyboardButton(text="💳 Оплатить 25₽", callback_data="buy_land_map")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_shop")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Generate confirmation keyboard"""
    keyboard = [
        [InlineKeyboardButton(text="✅ Да, подтверждаю", callback_data="confirm_land_map")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_shop")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_confirm_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Generate admin confirmation keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Отправить товар", callback_data=f"send_land_map_{user_id}"),
            InlineKeyboardButton(text="❌ Отменить покупку", callback_data=f"cancel_land_map_{user_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.callback_query(F.data == "shop_land_map")
async def show_land_map_info(callback: CallbackQuery):
    """Show land map product information"""
    try:
        await callback.message.edit_text(
            text=(
                "🗺 <b>Land Map - ваш путь к победе!</b>\n\n"
                "📍 Что включает в себя Land Map:\n"
                "• Детальные карты всех локаций\n"
                "• Оптимальные точки для высадки\n"
                "• Секретные позиции для засад\n"
                "• Маршруты для быстрого лута\n"
                "• Тактические точки для командной игры\n\n"
                "💡 С этими картами вы всегда будете на шаг впереди противников!\n\n"
                "💰 Стоимость: 25₽"
            ),
            reply_markup=get_land_map_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        await callback.message.answer(f"❌ Произошла ошибка: {str(e)}")

@router.callback_query(F.data == "buy_land_map") 
async def confirm_purchase(callback: CallbackQuery):
    """Show purchase confirmation"""
    try:
        await callback.message.edit_text(
            text="Вы уверены, что хотите приобрести Land Map за 25₽❓",
            reply_markup=get_confirm_keyboard()
        )
    except Exception as e:
        await callback.message.answer(f"❌ Произошла ошибка: {str(e)}")

@router.callback_query(F.data == "confirm_land_map")
async def process_purchase(callback: CallbackQuery):
    """Process land map purchase"""
    try:
        user_id = str(callback.from_user.id)
        username = callback.from_user.username or "Без username"
        full_name = callback.from_user.full_name
        
        user = db.get_user(telegram_id=user_id)
        if not user:
            await callback.message.edit_text(
                "❌ Пользователь не найден в базе данных",
                reply_markup=to_home_menu_inline()
            )
            return
            
        if user[3] < LAND_MAP_PRICE:
            await callback.message.edit_text(
                text=(
                    "❌ У вас недостаточно средств для покупки Land Map.\n"
                    f"Необходимо: {LAND_MAP_PRICE}₽\n"
                    f"Ваш баланс: {user[3]}₽"
                ),
                reply_markup=get_land_map_keyboard()
            )
            return

        # Deduct balance
        db.update_user(telegram_id=user_id, balance=-LAND_MAP_PRICE)

        await callback.message.edit_text(
            text="✅ Оплата прошла успешно!\nОжидайте подтверждения от администратора.",
            reply_markup=to_home_menu_inline()
        )
        
        # Notify admins
        await callback.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=(
                f"🛍 Новая покупка Land Map!\n\n"
                f"👤 Покупатель: {full_name}\n"
                f"🆔 ID: {user_id}\n"
                f"📝 Username: @{username}\n"
                f"💰 Сумма: {LAND_MAP_PRICE}₽"
            ),
            reply_markup=get_admin_confirm_keyboard(user_id)
        )
    except Exception as e:
        await callback.message.answer(f"❌ Произошла ошибка: {str(e)}")

@router.callback_query(F.data.startswith("send_land_map_"))
async def admin_send_land_map(callback: CallbackQuery, state: FSMContext):
    """Admin handler for sending land map"""
    try:
        user_id = callback.data.split("_")[-1]
        await state.update_data(user_id=user_id)
        await callback.message.edit_text(
            "📤 Отправьте фотографии Land Map одним сообщением"
        )
        await state.set_state(LandMapStates.waiting_land_map_photos)
    except Exception as e:
        await callback.message.answer(f"❌ Произошла ошибка: {str(e)}")

@router.callback_query(F.data.startswith("cancel_land_map_"))
async def admin_cancel_purchase(callback: CallbackQuery):
    """Admin handler for canceling purchase"""
    try:
        user_id = callback.data.split("_")[-1]
        
        # Return balance to user
        db.update_user(telegram_id=user_id, balance=LAND_MAP_PRICE)
        
        await callback.bot.send_message(
            chat_id=user_id,
            text=(
                "❌ К сожалению, ваша покупка Land Map была отменена.\n"
                "💰 Средства возвращены на ваш баланс.\n"
                "📞 Пожалуйста, обратитесь в поддержку для выяснения причины."
            ),
            reply_markup=to_home_menu_inline()
        )
        await callback.message.edit_text("✅ Покупка отменена, средства возвращены пользователю")
    except Exception as e:
        await callback.message.answer(f"❌ Произошла ошибка: {str(e)}")

@router.message(LandMapStates.waiting_land_map_photos)
async def process_land_map_photos(message: Message, state: FSMContext):
    """Process and send land map photos to user"""
    try:
        if not message.photo:
            await message.edit_text("❌ Пожалуйста, отправьте фотографии Land Map")
            return

        data = await state.get_data()
        user_id = data.get("user_id")
        
        if not user_id:
            await message.edit_text("❌ Ошибка: ID пользователя не найден")
            await state.clear()
            return

        # Отправляем товар пользователю
        await message.bot.send_photo(
            chat_id=user_id,
            photo=message.photo[-1].file_id,
            caption=(
                "🎉 Поздравляем с приобретением Land Map!\n\n"
                "🗺 Теперь у вас есть доступ к эксклюзивным картам и позициям.\n"
                "📌 Используйте их с умом для достижения победы!\n\n"
                "Приятной игры! 🎮"
            )
        )

        # Добавляем кнопку для отзыва
        review_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⭐️ Оставить отзыв", callback_data=f"leave_reviews_{user_id}_{LAND_MAP_PRICE}")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
        ])
        
        await message.bot.send_message(
            chat_id=user_id,
            text="Будем благодарны за ваш отзыв о покупке!",
            reply_markup=review_keyboard
        )
        
        await state.clear()
        await message.edit_text("✅ Land Map успешно отправлен пользователю")
    except Exception as e:
        await message.edit_text(f"❌ Произошла ошибка: {str(e)}")
        await state.clear()
