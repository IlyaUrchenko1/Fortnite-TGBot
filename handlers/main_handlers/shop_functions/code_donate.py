from aiogram import F
from aiogram import Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from utils.database import Database
from keyboards.user_keyboards import to_home_menu_inline

router = Router()
db = Database()

ADMIN_GROUP_CHAT_ID = -1002389059389

# Состояния
class DonateStates(StatesGroup):
    choosing_type = State()
    choosing_package = State()
    confirming = State()
    entering_credentials = State()
    entering_code = State()
    admin_confirmation = State()

# Общие клавиатуры
menu_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]]
)

back_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="go_back")]]
)

# Клавиатуры для доната
keyboard_donate_type = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="💻 С заходом на аккаунт", callback_data="donate_with_login")],
        [InlineKeyboardButton(text="🚫 Без захода на аккаунт", callback_data="donate_without_login")]
    ]
)

admin_confirm_keyboard_no_login = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="📞 Связаться", callback_data="admin_contact"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="admin_cancel"),
        InlineKeyboardButton(text="✅ Отправить код", callback_data="admin_send_code")
    ]
])

admin_confirm_keyboard_login = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="📞 Связаться", callback_data="admin_contact"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="admin_cancel"),
        InlineKeyboardButton(text="✅ Подтвердить зачисление", callback_data="admin_confirm_donate")
    ]
])

packages_keyboard = {
    "with_login": InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1000 в-баксов - 950₽", callback_data="package_1000_login")],
            [InlineKeyboardButton(text="2800 в-баксов - 1800₽", callback_data="package_2800_login")],
            [InlineKeyboardButton(text="5000 в-баксов - 2600₽", callback_data="package_5000_login")],
            [InlineKeyboardButton(text="13500 в-баксов - 6500₽", callback_data="package_13500_login")]
        ]
    ),
    "without_login": InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1000 в-баксов - 1300₽", callback_data="package_1000_nologin")],
            [InlineKeyboardButton(text="2800 в-баксов - 2150₽", callback_data="package_2800_nologin")],
            [InlineKeyboardButton(text="5000 в-баксов - 2950₽", callback_data="package_5000_nologin")],
            [InlineKeyboardButton(text="13500 в-баксов - 6850₽", callback_data="package_13500_nologin")]
        ]
    )
}

confirm_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="code_confirm_donate")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="code_cancel_donate")]
    ]
)


# Старт доната
@router.callback_query(F.data == "shop_code_donate")
async def donate_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "✨ Выберите тип доната:",
        reply_markup=keyboard_donate_type
    )
    await state.set_state(DonateStates.choosing_type)

# Выбор типа доната
@router.callback_query(F.data.startswith("donate_"))
async def donate_choose_type(callback: CallbackQuery, state: FSMContext):
    donate_type = callback.data.split("_", 1)[1]
    await state.update_data(donate_type=donate_type)
    await callback.message.edit_text(
        "📦 Выберите пакет:",
        reply_markup=packages_keyboard.get(donate_type, packages_keyboard["without_login"])
    )
    await state.set_state(DonateStates.choosing_package)

# Выбор пакета
@router.callback_query(F.data.startswith("package_"))
async def donate_choose_package(callback: CallbackQuery, state: FSMContext):
    package_data = callback.data.split("_")
    amount, login_type = package_data[1], package_data[2]

    prices = {
        "1000": "950₽" if login_type == "login" else "1300₽",
        "2800": "1800₽" if login_type == "login" else "2150₽",
        "5000": "2600₽" if login_type == "login" else "2950₽",
        "13500": "6500₽" if login_type == "login" else "6850₽"
    }

    try:
        price = prices[amount]
    except KeyError:
        await callback.message.edit_text(
            "❌ Выбранный пакет не существует. Пожалуйста, попробуйте снова.",
            reply_markup=menu_keyboard
        )
        await state.clear()
        return

    await state.update_data(amount=amount, price=price)

    await callback.message.edit_text(
        f"🎉 Вы выбрали {amount} в-баксов за {price}. Подтверждаете?",
        reply_markup=confirm_keyboard
    )
    await state.set_state(DonateStates.confirming)


@router.callback_query(F.data == "code_cancel_donate")
async def donate_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Донат отменен. Вы можете вернуться в главное меню.", reply_markup=to_home_menu_inline())
    await state.clear()
    await callback.answer()

# Обработчик подтверждения доната
@router.callback_query(F.data == "code_confirm_donate")
async def donate_confirm(callbacuser_idk: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    donate_type = user_data.get("donate_type")
    
    if donate_type == "with_login":
        await callback.message.edit_text("🔑 Пожалуйста, введите ваш ник и пароль через пробел.")
        await state.set_state(DonateStates.entering_credentials)
    elif donate_type == "without_login":
        user_id = callback.from_user.id  # Получаем ID пользователя напрямую
        
        await callback.message.bot.send_message(
            ADMIN_GROUP_CHAT_ID, 
            f"🔔 Пользователь купил код на {user_data.get('amount')} в-баксов за {user_data.get('price')} рублей. Отправьте ему код.", 
            reply_markup=admin_confirm_keyboard_no_login
        )
        
        await callback.message.edit_text("✅ Ваши данные отправлены администратору. Ожидайте подтверждения.", reply_markup=to_home_menu_inline())
        await state.update_data(user_id=user_id)  # Сохраняем user_id в состоянии
        await state.set_state(DonateStates.admin_confirmation)
        
    await callback.answer()

@router.callback_query(F.data == "admin_confirm_donate")
async def donate_confirm_admin(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
  
    data = await state.get_data()
    user_id = data.get("user_id")
  
    if user_id:
        await callback.message.bot.send_message(user_id, "✅ Ваш донат подтвержден. Вы можете зайти на аккаунт и проверить баланс.")
        await callback.message.bot.send_message(user_id, "По всем вопросам обращайтесь в нашу поддержку.")
    else:
        await callback.message.edit_text("❌ Не удалось найти пользователя для подтверждения доната.")
  
    await callback.message.bot.send_message(ADMIN_GROUP_CHAT_ID, "✅ Донат успешно подтвержден.")
    await state.clear()

@router.message(DonateStates.entering_credentials)
async def donate_enter_credentials(message: Message, state: FSMContext):
		msg = message.text.split(" ")
		nickname = msg[0]
		password = msg[1]
  

		data = await state.get_data()
		amount = data.get("amount")
		price = data.get("price")
  
		await state.update_data(user_id=message.from_user.id)
  
		await message.bot.send_message(ADMIN_GROUP_CHAT_ID, f"🔔 Пользователь купил код на {amount} в-баксов за {price} рублей. Ник: {nickname}, Пароль: {password}", reply_markup=admin_confirm_keyboard_login)
  
    

