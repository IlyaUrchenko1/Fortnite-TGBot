from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards.shop_keyboards import get_back_to_shop_keyboard
from utils.database import Database

router = Router()
db = Database()

LAND_MAP_PRICE = 25
ADMIN_GROUP_ID = -1002389059389

class LandMapStates(StatesGroup):
    waiting_land_map_photos = State()

def get_land_map_keyboard() -> InlineKeyboardBuilder:
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="💳 Оплатить 25₽", callback_data="buy_land_map"))
    keyboard.row(InlineKeyboardButton(text="◀️ Назад в магазин", callback_data="shop"))
    return keyboard.as_markup()

def get_confirm_keyboard() -> InlineKeyboardBuilder:
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="✅ Да, подтверждаю", callback_data="confirm_land_map"))
    keyboard.row(InlineKeyboardButton(text="❌ Отмена", callback_data="shop_land_map"))
    return keyboard.as_markup()

def get_admin_confirm_keyboard(user_id: int) -> InlineKeyboardBuilder:
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text="✅ Отправить товар", callback_data=f"send_land_map_{user_id}"),
        InlineKeyboardButton(text="❌ Отменить покупку", callback_data=f"cancel_land_map_{user_id}")
    )
    return keyboard.as_markup()

@router.callback_query(F.data == "shop_land_map")
async def show_land_map_info(callback: CallbackQuery):
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
        reply_markup=get_land_map_keyboard()
    )

@router.callback_query(F.data == "buy_land_map")
async def confirm_purchase(callback: CallbackQuery):
    await callback.message.edit_text(
        text="Вы уверены, что хотите приобрести Land Map за 25₽❓",
        reply_markup=get_confirm_keyboard()
    )

@router.callback_query(F.data == "confirm_land_map")
async def process_purchase(callback: CallbackQuery):
    # Here should be balance check and deduction logic
    user_id = callback.from_user.id
    username = callback.from_user.username or "Без username"
    full_name = callback.from_user.full_name
    
    user = db.get_user(telegram_id=user_id)
    if user[3] < LAND_MAP_PRICE:
        await callback.message.edit_text(
            text="❌ У вас недостаточно средств для покупки Land Map.",
            reply_markup=get_back_to_shop_keyboard()
        )
        return
    db.update_user(telegram_id=user_id, balance=user[3] - LAND_MAP_PRICE)

    await callback.message.edit_text(
        text="✅ Оплата прошла успешно!\nОжидайте подтверждения от администратора.",
        reply_markup=get_back_to_shop_keyboard()
    )
    
    # Sending notification to admin group
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

@router.callback_query(F.data.startswith("send_land_map_"))
async def admin_send_land_map(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[-1])
    await state.set_state(LandMapStates.waiting_land_map_photos)
    await state.update_data(user_id=user_id)
    await callback.message.edit_text(
        "📤 Отправьте фотографии Land Map одним сообщением"
    )

@router.callback_query(F.data.startswith("cancel_land_map_"))
async def admin_cancel_purchase(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[-1])
    # Here should be balance return logic
    await callback.bot.send_message(
        chat_id=user_id,
        text=(
            "❌ К сожалению, ваша покупка Land Map была отменена.\n"
            "📞 Пожалуйста, обратитесь в поддержку для выяснения причины."
        ),
        reply_markup=get_back_to_shop_keyboard()
    )
    await callback.message.edit_text("Покупка отменена")

@router.message(LandMapStates.waiting_land_map_photos)
async def process_land_map_photos(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("Пожалуйста, отправьте фотографии Land Map одним сообщением.")
        return

    data = await state.get_data()
    user_id = data["user_id"]
    # Send photos to user
    await message.copy_to(
        chat_id=user_id,
        caption=(
            "🎉 Поздравляем с приобретением Land Map!\n\n"
            "🗺 Теперь у вас есть доступ к эксклюзивным картам и позициям.\n"
            "📌 Используйте их с умом для достижения победы!\n\n"
            "Приятной игры! 🎮"
        )
    )
    
    await state.clear()
    await message.answer("✅ Land Map успешно отправлен пользователю")
