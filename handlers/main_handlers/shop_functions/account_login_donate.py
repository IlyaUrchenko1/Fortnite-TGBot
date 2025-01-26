from aiogram import F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from utils.database import Database
from keyboards.user_keyboards import to_home_menu_inline
from utils.constants import GROUP_ID_SERVICE_PROVIDER

router = Router()
db = Database()

class AccountLoginStates(StatesGroup):
    choosing_package = State()
    confirming = State()
    entering_credentials = State()
    admin_confirmation = State()

def get_packages_keyboard():
    packages = [
        ("1000 в-баксов - 950₽", "acc_package_1000"),
        ("2800 в-баксов - 1800₽", "acc_package_2800"), 
        ("5000 в-баксов - 3000₽", "acc_package_5000"),
        ("13500 в-баксов - 6500₽", "acc_package_13500")
    ]
    
    buttons = [[InlineKeyboardButton(text=text, callback_data=data)] 
               for text, data in packages]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_shop")])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_keyboard():
    buttons = [
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="acc_confirm_donate")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="acc_cancel_donate")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_packages")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.callback_query(F.data == "shop_account_donate")
async def account_donate_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🎮 <b>Донат через вход в аккаунт</b>\n\n"
        "ℹ️ Мы зайдем в ваш аккаунт, изменим регион и пополним в-баксы.\n"
        "Выберите желаемый пакет:",
        reply_markup=get_packages_keyboard()
    )
    await state.set_state(AccountLoginStates.choosing_package)

@router.callback_query(F.data == "back_to_packages")
async def back_to_packages(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🎮 Выберите желаемый пакет:",
        reply_markup=get_packages_keyboard()
    )
    await state.set_state(AccountLoginStates.choosing_package)

@router.callback_query(F.data.startswith("acc_package_"))
async def account_choose_package(callback: CallbackQuery, state: FSMContext):
    amount = callback.data.split("_")[2]
    
    prices = {
        "1000": "950₽",
        "2800": "1800₽",
        "5000": "3000₽",
        "13500": "6500₽"
    }

    try:
        price = prices[amount]
        price_num = int(price.replace("₽", ""))
        user_balance = db.get_user(str(callback.from_user.id)).get("balance", 0)
        
        if user_balance < price_num:
            await callback.message.edit_text(
                f"❌ На вашем балансе недостаточно средств!\n\n"
                f"💰 Ваш баланс: {user_balance}₽\n"
                f"💵 Стоимость пакета: {price}\n"
                f"🔄 Необходимо пополнить: {price_num - user_balance}₽",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="add_balance")],
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_packages")],
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
                ])
            )
            return

        await state.update_data(amount=amount, price=price)
        await callback.message.edit_text(
            f"🎉 Вы выбрали {amount} в-баксов за {price}\n\n"
            "⚠️ После подтверждения вам нужно будет отправить данные от аккаунта.\n"
            "Подтверждаете выбор?",
            reply_markup=get_confirm_keyboard()
        )
        await state.set_state(AccountLoginStates.confirming)
    except KeyError:
        await callback.message.edit_text(
            "❌ Выбранный пакет не существует. Попробуйте снова.",
            reply_markup=get_packages_keyboard()
        )

@router.callback_query(F.data == "acc_cancel_donate")
async def account_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "❌ Донат отменен. Вы можете вернуться в главное меню или начать заново.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="shop_account_donate")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
        ])
    )
    await state.clear()

@router.callback_query(F.data == "acc_confirm_donate")
async def account_confirm(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_packages")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
    ])
    
    await callback.message.edit_text(
        "✏️ Пожалуйста, отправьте данные от вашего аккаунта в формате:\n"
        "<code>логин пароль</code>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(AccountLoginStates.entering_credentials)

@router.message(AccountLoginStates.entering_credentials)
async def process_credentials(message: Message, state: FSMContext):
    try:
        await message.delete()  # Удаляем сообщение с учетными данными
        
        credentials = message.text.split()
        if len(credentials) != 2:
            raise ValueError("Необходимо отправить логин и пароль через пробел")
            
        login, password = credentials
        data = await state.get_data()
        
        admin_message = (
            "🎮 <b>Новый донат через вход в аккаунт!</b>\n\n"
            f"👤 Покупатель: {message.from_user.full_name}\n"
            f"🔗 Username: @{message.from_user.username}\n"
            f"🆔 ID: <code>{message.from_user.id}</code>\n"
            f"💰 Пакет: {data['amount']} в-баксов\n"
            f"💵 Сумма: {data['price']}\n"
            f"📧 Логин: {login}\n"
            f"🔑 Пароль: {password}"
        )

        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📱 Связаться", url=f"tg://user?id={message.from_user.id}")],
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"admin_acc_confirm_{message.from_user.id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_acc_reject_{message.from_user.id}")
            ]
        ])

        await message.bot.send_message(
            GROUP_ID_SERVICE_PROVIDER,
            admin_message,
            reply_markup=admin_keyboard,
            parse_mode="HTML"
        )

        await message.answer(
            "✅ Ваша заявка отправлена администратору!\n"
            "⏳ Ожидайте подтверждения.",
            reply_markup=to_home_menu_inline()
        )
        await state.clear()

    except Exception as e:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Попробовать снова", callback_data="acc_confirm_donate")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
        ])
        
        await message.answer(
            f"❌ Ошибка: {str(e)}\nПопробуйте еще раз.",
            reply_markup=keyboard
        )

@router.callback_query(F.data.startswith("admin_acc_confirm_"))
async def admin_confirm_account(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[3])
    
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⭐️ Оставить отзыв", callback_data=f"leave_reviews_{user_id}")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
        ])
        
        await callback.bot.send_message(
            user_id,
            "✅ Ваша заявка подтверждена!\n"
            "⏳ Администратор скоро выполнит пополнение.",
            reply_markup=keyboard
        )
        
        await callback.message.edit_text(
            callback.message.text + "\n\n✅ Заявка подтверждена",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await callback.answer(f"Ошибка: {str(e)}")

@router.callback_query(F.data.startswith("admin_acc_reject_"))
async def admin_reject_account(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[3])
    
    try:
        await callback.bot.send_message(
            user_id,
            "❌ Ваша заявка отклонена администратором.\n"
            "Пожалуйста, свяжитесь с поддержкой.",
            reply_markup=to_home_menu_inline()
        )
        
        await callback.message.edit_text(
            callback.message.text + "\n\n❌ Заявка отклонена",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await callback.answer(f"Ошибка: {str(e)}")
