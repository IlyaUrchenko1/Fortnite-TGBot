from aiogram import F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from utils.database import Database
from keyboards.user_keyboards import to_home_menu_inline
from utils.constants import GROUP_ID_SERVICE_PROVIDER

router = Router()
db = Database()

class DonateStates(StatesGroup):
    choosing_package = State()
    confirming = State()
    entering_code = State()
    admin_confirmation = State()

def get_navigation_keyboard(include_back=True, include_home=True, back_callback="go_back"):
    buttons = []
    if include_back:
        buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=back_callback))
    if include_home:
        buttons.append(InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

def get_packages_keyboard():
    packages = [
        ("1000 в-баксов - 1300₽", "package_1000"),
        ("2800 в-баксов - 2800₽", "package_2800"),
        ("5000 в-баксов - 4700₽", "package_5000"),
        ("13500 в-баксов - 11000₽", "package_13500")
    ]
    
    buttons = [[InlineKeyboardButton(text=text, callback_data=data)] 
               for text, data in packages]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_shop")])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_keyboard():
    buttons = [
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="code_confirm_donate")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="code_cancel_donate")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_packages")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_confirm_keyboard(user_id: int):
    buttons = [
        [
            InlineKeyboardButton(text="📞 Связаться", callback_data=f"admin_contact_{user_id}"),
            InlineKeyboardButton(text="❌ Отменить", callback_data=f"admin_cancel_{user_id}")
        ],
        [
            InlineKeyboardButton(text="✅ Отправить код", callback_data=f"admin_send_code_{user_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.callback_query(F.data == "shop_code_donate")
async def donate_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🎁 Выберите желаемый код:",
        reply_markup=get_packages_keyboard()
    )
    await state.set_state(DonateStates.choosing_package)

@router.callback_query(F.data == "back_to_packages") 
async def back_to_packages(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🎁 Выберите желаемый код:",
        reply_markup=get_packages_keyboard()
    )
    await state.set_state(DonateStates.choosing_package)

@router.callback_query(F.data.startswith("package_"))
async def donate_choose_package(callback: CallbackQuery, state: FSMContext):
    amount = callback.data.split("_")[1]

    prices = {
        "1000": "1300₽",
        "2800": "2800₽",
        "5000": "4700₽",
        "13500": "11000₽"
    }

    try:
        price = prices[amount]
        await state.update_data(amount=amount, price=price)
        await callback.message.edit_text(
            f"🎉 Вы выбрали {amount} в-баксов за {price}. Подтверждаете?",
            reply_markup=get_confirm_keyboard()
        )
        await state.set_state(DonateStates.confirming)
    except KeyError:
        await callback.message.edit_text(
            "❌ Выбранный пакет не существует. Пожалуйста, попробуйте снова.",
            reply_markup=get_navigation_keyboard(back_callback="shop_code_donate")
        )
        await state.set_state(DonateStates.choosing_package)

@router.callback_query(F.data == "code_cancel_donate")
async def donate_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "❌ Донат отменен. Вы можете вернуться в главное меню или начать заново.", 
        reply_markup=get_navigation_keyboard(back_callback="shop_code_donate")
    )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "code_confirm_donate")
async def donate_confirm(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    user_id = callback.from_user.id
    await state.update_data(user_id=user_id)
    
    await callback.message.bot.send_message(
        GROUP_ID_SERVICE_PROVIDER,
        f"🔔 Пользователь @{callback.from_user.username or 'Без username'} (ID: {user_id}) "
        f"купил код на {user_data.get('amount')} в-баксов за {user_data.get('price')} рублей.",
        reply_markup=get_admin_confirm_keyboard(user_id)
    )
    await callback.message.edit_text(
        "✅ Ваши данные отправлены администратору. Ожидайте подтверждения.", 
        reply_markup=to_home_menu_inline()
    )
    await state.set_state(DonateStates.admin_confirmation)

@router.callback_query(F.data.startswith("admin_cancel_"))
async def donate_admin_cancel(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[-1])
    try:
        await callback.message.bot.send_message(
            user_id,
            "❌ Ваш донат был отменен администратором. Пожалуйста, свяжитесь с поддержкой.",
            reply_markup=to_home_menu_inline()
        )
        await callback.message.edit_text(f"❌ Донат отменен для пользователя {user_id}.")
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при отмене доната: {str(e)}")
    await state.clear()
    await callback.answer()

@router.callback_query(F.data.startswith("admin_contact_"))
async def donate_admin_contact(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[-1])
    try:
        await callback.message.bot.send_message(
            user_id,
            "👋 Администратор скоро свяжется с вами для уточнения деталей.",
            reply_markup=to_home_menu_inline()
        )
        await callback.message.edit_text(f"✉️ Сообщение о связи отправлено пользователю (ID: {user_id})")
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при отправке сообщения: {str(e)}")
    await callback.answer()

@router.callback_query(F.data.startswith("admin_send_code_"))
async def donate_admin_send_code(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[-1])
    await state.update_data(user_id=user_id)
    await callback.message.edit_text("📝 Введите код, который нужно отправить пользователю:")
    await state.set_state(DonateStates.entering_code)
    await callback.answer()

@router.message(DonateStates.entering_code)
async def donate_process_code(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        user_id = data.get("user_id")
        
        if not user_id:
            await message.answer(
                "❌ Не удалось отправить код пользователю: ID пользователя не найден",
                reply_markup=to_home_menu_inline()
            )
            await state.clear()
            return
            
        if not message.text:
            await message.answer(
                "❌ Код не может быть пустым. Попробуйте еще раз.",
                reply_markup=get_navigation_keyboard()
            )
            return
            
        # Отправляем код пользователю
        await message.bot.send_message(
            user_id,
            f"🎮 Ваш код: {message.text}\n\n"
            "Инструкция по активации:\n"
            "1. Зайдите в игру\n"
            "2. Перейдите в раздел 'Активация кода'\n"
            "3. Введите полученный код",
            reply_markup=to_home_menu_inline()
        )
        
        # Добавляем кнопку для отзыва
        review_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⭐️ Оставить отзыв", callback_data=f"leave_reviews_{user_id}_{data.get('price')}")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
        ])
        
        await message.bot.send_message(
            user_id,
            "Будем благодарны за ваш отзыв о покупке!",
            reply_markup=review_keyboard
        )
        
        await message.answer("✅ Код успешно отправлен пользователю.")
        await state.clear()
        
    except Exception as e:
        await message.answer(
            f"❌ Произошла ошибка при отправке кода: {str(e)}",
            reply_markup=to_home_menu_inline()
        )
        await state.clear()
