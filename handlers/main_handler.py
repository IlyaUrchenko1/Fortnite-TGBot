from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.user_keyboards import start_bot_menu, admin_menu
from keyboards.shop_keyboards import get_fortnite_shop_main_keyboard, get_brawl_stars_shop_main_keyboard
from utils.database import Database
from utils.constants import ADMIN_IDS

router = Router()
db = Database()


@router.message(CommandStart())
async def start_command(message: Message, command: CommandStart = None):
    try:
        await message.delete()
        
        if message.from_user.id in ADMIN_IDS:
            await message.bot.send_message(chat_id=message.chat.id, text="Поскольку вы админ, вы можете использовать следующие команды:", reply_markup=admin_menu())


        user_id = str(message.from_user.id)
        username = message.from_user.username or "Пользователь"
        
        # Проверяем существует ли пользователь в БД
        is_new_user = not db.is_exists(user_id)
        
        if is_new_user:
            try:
                # Получаем ID реферера из команды старт (если есть)
                try:
                    referrer_id = int(command.args) if command and command.args and command.args.isdigit() else None
                    # Добавляем нового пользователя
                    db.add_user(user_id, username, referrer_id)
                except (ValueError, TypeError):
                    # Если не удалось преобразовать ID реферера, добавляем пользователя без реферера
                    db.add_user(user_id, username, None)
                
                welcome_text = (
                    f"👋 Добро пожаловать, {username}!\n\n"
                    "🎮 Вы попали в официального бота по продаже V-Bucks для Fortnite.\n"
                    "💫 У нас самые выгодные цены и быстрая поддержка!\n\n"
                    "▶️ Выберите интересующий раздел в меню ниже 👇\n"
                    "❓ Остались вопросы? Наша поддержка всегда на связи!"
                )
            except ValueError:
                # Если возникла ошибка при конвертации referrer_id
                welcome_text = "⚠️ Произошла ошибка при обработке реферальной ссылки. Пожалуйста, попробуйте еще раз."
        else:
            welcome_text = (
                f"🎉 С возвращением, {username}!\n\n"
                "💎 Рады видеть вас снова в нашем магазине V-Bucks.\n"
                "▶️ Выберите нужный раздел в меню ниже 👇"
            )

        # Отправляем приветственное сообщение
        await message.bot.send_message(
            chat_id=message.chat.id,
            text=welcome_text,
            reply_markup=start_bot_menu()
        )
        
        # Отправляем стикер
        await message.bot.send_sticker(
            chat_id=message.chat.id,
            sticker="CAACAgUAAxkBAAKaVWdcYC51Dyz9QQpepSLGgOPQK_MMAAJdEQACr3tRVZEquUWHNk4oNgQ"
        )
        
                
    except Exception as e:
        error_message = f"❌ Произошла ошибка при обработке команды: {str(e)}"
        await message.bot.send_message(chat_id=message.chat.id, text=error_message)


@router.message(F.text == "🏠 Вернуться назад")
async def return_to_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.delete()
    await message.answer("⬇️ Вы вернулись в главное меню ⬇️", reply_markup=start_bot_menu())
    
@router.callback_query(F.data == "to_home_menu")
async def return_to_home(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        await callback.message.edit_text("⬇️ Вы вернулись в главное меню ⬇️", reply_markup=start_bot_menu())
    except:
        await callback.message.answer("⬇️ Вы вернулись в главное меню ⬇️", reply_markup=start_bot_menu())
    await state.clear()

@router.callback_query(F.data == "back_to_shop")
async def back_to_shop(callback: CallbackQuery):
    """Return to main shop menu"""
    try:
        try:
            await callback.message.bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id + 1
            )
        except:
            pass

        games_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎮 Fortnite", callback_data="fortnite_shop")],
            [InlineKeyboardButton(text="⭐️ Brawl Stars", callback_data="brawl_stars")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
        ])
        
        await callback.message.edit_text(
            text="🎮 Выберите игру для покупки:",
            reply_markup=games_keyboard
        )
    except:
        print("delete_message error in back_to_shop")
        pass
        
@router.callback_query(F.data == "back_to_admin_menu")
async def back_to_admin_menu(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("🔑 Админ-панель", reply_markup=admin_menu())


@router.message(F.text == "/get_id")
async def get_chat_id(message: Message):
    await message.answer(f"Chat id is: *{message.chat.id}*\nYour id is: *{message.from_user.id}*",
                             parse_mode='Markdown')
