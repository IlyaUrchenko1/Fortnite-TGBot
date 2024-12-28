from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest

from utils.database import Database
from keyboards.user_keyboards import back_to_admin_menu, admin_menu
from utils.constants import ADMIN_IDS

router = Router()
db = Database()

# Состояния FSM для рассылки
class NewsletterStates(StatesGroup):
    waiting_for_message = State()  # Ожидание текста рассылки
    waiting_for_photo = State()    # Ожидание фото для рассылки
    confirm_sending = State()      # Подтверждение отправки

def get_yes_no_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопками подтверждения/отмены"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text='✅ Подтвердить', callback_data='newsletter_confirm'),
        InlineKeyboardButton(text='❌ Отменить', callback_data='newsletter_cancel')
    )
    keyboard.row(
        InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_admin_menu'),
        InlineKeyboardButton(text='🏠 Главное меню', callback_data='to_home_menu')
    )
    return keyboard.as_markup()

def get_photo_choice_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру выбора добавления фото"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text='🖼 Добавить фото', callback_data='add_photo'),
        InlineKeyboardButton(text='⏭ Пропустить', callback_data='skip_photo')
    )
    keyboard.row(
        InlineKeyboardButton(text='⬅️ Назад', callback_data='back_to_admin_menu'),
        InlineKeyboardButton(text='🏠 Главное меню', callback_data='to_home_menu')
    )
    return keyboard.as_markup()

@router.callback_query(F.data == "start_newsletter")
async def start_newsletter(callback: CallbackQuery, state: FSMContext):
    """Начало создания рассылки"""
    await callback.answer()
    
    # Проверка прав администратора
    if callback.from_user.id not in ADMIN_IDS:
        await callback.message.answer("❌ У вас нет прав для выполнения этой команды!")
        return
    
    try:
        await callback.message.edit_text(
            "📨 <b>Создание рассылки</b>\n\n"
            "Введите текст сообщения для рассылки:",
            reply_markup=back_to_admin_menu(),
            parse_mode="HTML"
        )
        await state.set_state(NewsletterStates.waiting_for_message)
    except TelegramBadRequest:
        await callback.message.answer(
            "📨 <b>Создание рассылки</b>\n\n"
            "Введите текст сообщения для рассылки:",
            reply_markup=back_to_admin_menu(),
            parse_mode="HTML"
        )
        await state.set_state(NewsletterStates.waiting_for_message)

@router.message(NewsletterStates.waiting_for_message)
async def process_newsletter_message(message: Message, state: FSMContext):
    """Обработка введенного текста рассылки"""
    if not message.text:
        await message.answer("❌ Пожалуйста, отправьте текстовое сообщение")
        return
        
    await state.update_data(text=message.text)
    await message.answer(
        "🎨 Хотите добавить фото к рассылке?",
        reply_markup=get_photo_choice_keyboard()
    )
    await state.set_state(NewsletterStates.waiting_for_photo)

@router.callback_query(NewsletterStates.waiting_for_photo, F.data == "add_photo")
async def add_photo(callback: CallbackQuery):
    """Запрос на добавление фото"""
    await callback.answer()
    await callback.message.edit_text(
        "📸 Отправьте фото для рассылки\n"
        "❗️ Фото должно быть отправлено как фото, а не файл"
    )

@router.callback_query(NewsletterStates.waiting_for_photo, F.data == "skip_photo")
async def skip_photo(callback: CallbackQuery, state: FSMContext):
    """Пропуск добавления фото"""
    await callback.answer()
    data = await state.get_data()
    
    preview = f"📋 Предварительный просмотр:\n\n{data['text']}"
    await callback.message.edit_text(
        preview,
        reply_markup=get_yes_no_keyboard()
    )
    await state.set_state(NewsletterStates.confirm_sending)

@router.message(NewsletterStates.waiting_for_photo, F.photo)
async def process_newsletter_photo(message: Message, state: FSMContext):
    """Обработка полученного фото"""
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    
    data = await state.get_data()
    
    try:
        await message.answer_photo(
            photo=photo_id,
            caption=f"📋 Предварительный просмотр:\n\n{data['text']}",
            reply_markup=get_yes_no_keyboard()
        )
        await state.set_state(NewsletterStates.confirm_sending)
    except TelegramBadRequest as e:
        await message.answer(
            "❌ Ошибка при обработке фото. Попробуйте другое фото или пропустите этот шаг",
            reply_markup=get_photo_choice_keyboard()
        )

@router.callback_query(NewsletterStates.confirm_sending, F.data == "newsletter_confirm")
async def send_newsletter(callback: CallbackQuery, state: FSMContext):
    """Отправка рассылки пользователям"""
    await callback.answer()
    data = await state.get_data()
    users = db.get_all_users()

    sent_count = 0
    failed_count = 0
    
    status_message = await callback.message.edit_text(
        "📨 Начинаю рассылку...\n"
        "⏳ Пожалуйста, подождите"
    )
    
    for user in users:
        if user[6]:  # Пропускаем забаненных пользователей
            continue
            
        try:
            if 'photo_id' in data:
                await callback.bot.send_photo(
                    chat_id=user[1],
                    photo=data['photo_id'],
                    caption=data['text']
                )
            else:
                await callback.bot.send_message(
                    chat_id=user[1],
                    text=data['text']
                )
            sent_count += 1
        except Exception:
            failed_count += 1
            continue
    
    await status_message.edit_text(
        f"✅ Рассылка успешно завершена!\n\n"
        f"📨 Успешно отправлено: {sent_count}\n"
        f"❌ Не удалось отправить: {failed_count}",
        reply_markup=admin_menu()
    )
    await state.clear()

@router.callback_query(NewsletterStates.confirm_sending, F.data == "newsletter_cancel")
async def cancel_newsletter(callback: CallbackQuery, state: FSMContext):
    """Отмена рассылки"""
    await callback.answer()
    await callback.message.edit_text(
        "❌ Рассылка отменена",
        reply_markup=admin_menu()
    )
    await state.clear()
