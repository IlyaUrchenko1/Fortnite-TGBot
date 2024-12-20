from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

class SupportStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_content = State()
    waiting_for_admin_response = State()

@router.callback_query(F.data == "support")
async def start_support_dialog(callback: CallbackQuery, state: FSMContext):
		await callback.answer()
		await callback.message.answer("📝 Пожалуйста, напишите заголовок вашего обращения (до 100 слов)")
		await state.set_state(SupportStates.waiting_for_title)

@router.message(SupportStates.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    if message.photo:
        await message.answer("❌ Вы не можете прикреплять фото к заголовку.")
        return
  
    if (len(message.text.split()) > 100):
        await message.answer("❌ Заголовок слишком длинный! Пожалуйста, сократите его до 100 слов.")
        return

    
    await state.update_data(title=message.text)
    await message.answer("📨 Теперь опишите вашу проблему подробно. Вы можете прикрепить фото к сообщению.")
    await state.set_state(SupportStates.waiting_for_content)

@router.message(SupportStates.waiting_for_content)
async def process_content(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data['title']
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ответить", callback_data=f"answer_{message.from_user.id}"),
                InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{message.from_user.id}")
            ]
        ]
    )
    
    support_text = f"<h3>📋 Заголовок:</h3>\n{title}\n\n<h3>📝 Содержание:</h3>\n{message.text or 'Текст отсутствует'}"
    
    if message.photo:
        await message.bot.send_photo(
            chat_id="-1002360777828",
            photo=message.photo[-1].file_id,
            caption=support_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await message.bot.send_message(
            chat_id="-1002360777828",
            text=support_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    await message.answer("✅ Ваше обращение отправлено! Ожидайте ответа от администратора.")
    await state.clear()

@router.callback_query(F.data.startswith("answer_"))
async def admin_answer(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = int(callback.data.split("_")[1])
    await state.update_data(user_id=user_id)
    await callback.message.delete()
    await callback.message.answer("📝 Введите ответ пользователю. Вы можете прикрепить фото.")
    await state.set_state(SupportStates.waiting_for_admin_response)
    

@router.message(SupportStates.waiting_for_admin_response)
async def send_admin_response(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    
    response_text = "📨 <b>Ответ от администрации:</b>\n\n" + message.text
    
    if message.photo:
        await message.bot.send_photo(
            chat_id=user_id,
            photo=message.photo[-1].file_id,
            caption=response_text,
            parse_mode="HTML"
        )
    else:
        await message.bot.send_message(
            chat_id=user_id,
            text=response_text,
            parse_mode="HTML"
        )
    
    await message.answer("✅ Ответ отправлен пользователю!")
    await state.clear()

@router.callback_query(F.data.startswith("cancel_"))
async def cancel_request(callback: CallbackQuery):
    await callback.answer()
    
    user_id = int(callback.data.split("_")[1])
    await callback.message.delete()
    
    await callback.bot.send_message(
        chat_id=user_id,
        text="❌ К сожалению, ваше обращение было отклонено администрацией."
    )
  
