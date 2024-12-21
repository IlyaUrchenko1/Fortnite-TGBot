from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton


from utils.database import Database
from keyboards.user_keyboards import to_home_menu_inline

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
    return keyboard.as_markup()

def get_photo_choice_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text='🖼 Добавить фото', callback_data='add_photo'),
        InlineKeyboardButton(text='⏭ Пропустить', callback_data='skip_photo')
    )
    return keyboard.as_markup()

@router.callback_query(F.data == "start_newsletter")
async def start_newsletter(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
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
    await callback.message.answer(
        "📤 Отправьте фото для рассылки:",
        reply_markup=to_home_menu_inline()
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
    data = await state.get_data()
    
    preview = f"📋 Предварительный просмотр:\n\n{data['text']}"
    await callback.message.answer(preview)
    await callback.message.answer(
        "❓ Подтвердите отправку рассылки",
        reply_markup=get_yes_no_keyboard()
    )
    await state.set_state(NewsletterStates.confirm_sending)

@router.callback_query(NewsletterStates.confirm_sending, F.data == "newsletter_confirm")
async def send_newsletter(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    users = db.get_all_users()
    
    sent_count = 0
    failed_count = 0
    
    await callback.message.answer("📨 Начинаю рассылку...")
    
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
        reply_markup=to_home_menu_inline()
    )
    await state.clear()

@router.callback_query(NewsletterStates.confirm_sending, F.data == "newsletter_cancel")
async def cancel_newsletter(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "❌ Рассылка отменена",
        reply_markup=to_home_menu_inline()
    )
    await state.clear()

@router.callback_query(F.data == "to_home_menu", NewsletterStates)
async def cancel_newsletter_inline(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "❌ Рассылка отменена",
        reply_markup=to_home_menu_inline()
    )
    await state.clear()
