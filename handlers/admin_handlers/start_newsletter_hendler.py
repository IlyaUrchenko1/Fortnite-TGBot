from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton

from utils.database import Database
from keyboards.user_keyboards import to_home_menu_inline
from keyboards.user_keyboards import admin_menu, start_bot_menu

from utils.varibles import ADMIN_IDS

router = Router()
db = Database()

class NewsletterStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_photo = State()
    confirm_sending = State()

def get_yes_no_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text='✅ Да', callback_data='newsletter_confirm'),
        InlineKeyboardButton(text='❌ Нет', callback_data='newsletter_cancel')
    )
    keyboard.row(InlineKeyboardButton(text='◀️ Назад', callback_data='start_newsletter'))
    keyboard.row(InlineKeyboardButton(text='🏠 Главное меню', callback_data='to_home_menu'))
    return keyboard.as_markup()

def get_photo_choice_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text='🖼 Добавить фото', callback_data='add_photo'),
        InlineKeyboardButton(text='⏭ Пропустить', callback_data='skip_photo')
    )
    keyboard.row(InlineKeyboardButton(text='◀️ Назад', callback_data='start_newsletter'))
    keyboard.row(InlineKeyboardButton(text='🏠 Главное меню', callback_data='to_home_menu'))
    return keyboard.as_markup()

@router.callback_query(F.data == "start_newsletter")
async def start_newsletter(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.message.answer("❌ У вас нет прав для выполнения этой команды.")
        return

    await callback.message.edit_text(
        "📝 Введите текст сообщения для рассылки:\n\n"
        "Вы можете использовать HTML-разметку для форматирования текста.",
        reply_markup=to_home_menu_inline()
    )
    await state.set_state(NewsletterStates.waiting_for_message)

@router.message(NewsletterStates.waiting_for_message)
async def get_newsletter_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    
    await message.answer(
        "🖼 Хотите добавить фото к рассылке?",
        reply_markup=get_photo_choice_keyboard()
    )
    await state.set_state(NewsletterStates.waiting_for_photo)

@router.callback_query(NewsletterStates.waiting_for_photo, F.data == "add_photo")
async def request_photo(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "📤 Отправьте фото для рассылки:",
        reply_markup=get_photo_choice_keyboard()
    )

@router.message(NewsletterStates.waiting_for_photo, F.photo)
async def get_newsletter_photo(message: Message, state: FSMContext):
    await state.update_data(photo_id=message.photo[-1].file_id)
    data = await state.get_data()
    
    preview = f"📋 Предварительный просмотр:\n\n{data['text']}"
    await message.answer_photo(
        photo=data['photo_id'],
        caption=preview,
        reply_markup=get_yes_no_keyboard()
    )
    await message.answer(
        "❓ Подтвердите отправку рассылки"
    )
    await state.set_state(NewsletterStates.confirm_sending)

@router.callback_query(NewsletterStates.waiting_for_photo, F.data == "skip_photo")
async def skip_photo(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    
    preview = f"📋 Предварительный просмотр:\n\n{data['text']}"
    await callback.message.edit_text(preview)
    await callback.message.answer(
        "❓ Подтвердите отправку рассылки",
        reply_markup=get_yes_no_keyboard()
    )
    await state.set_state(NewsletterStates.confirm_sending)

@router.callback_query(NewsletterStates.confirm_sending, F.data == "newsletter_confirm")
async def send_newsletter(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    users = db.get_all_users()
    
    sent_count = 0
    failed_count = 0
    
    await callback.message.edit_text("📨 Начинаю рассылку...")
    
    for user in users:
        try:
            if 'photo_id' in data:
                await callback.message.bot.send_photo(
                    chat_id=user[1],  # telegram_id is at index 1
                    photo=data['photo_id'],
                    caption=data['text']
                )
            else:
                await callback.message.bot.send_message(
                    chat_id=user[1],
                    text=data['text']
                )
            sent_count += 1
        except Exception:
            failed_count += 1
            continue
    
    await callback.message.answer(
        f"✅ Рассылка успешно завершена!\n\n"
        f"📨 Успешно отправлено: {sent_count}\n"
        f"❌ Не удалось отправить: {failed_count}",
        reply_markup=admin_menu()
    )
    await state.clear()

@router.callback_query(NewsletterStates.confirm_sending, F.data == "newsletter_cancel")
async def cancel_newsletter(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        "❌ Рассылка отменена",
        reply_markup=admin_menu()
    )
    await state.clear()
