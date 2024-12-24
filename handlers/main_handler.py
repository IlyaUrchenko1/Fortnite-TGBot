from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from keyboards.user_keyboards import start_bot_menu, admin_menu
from utils.database import Database
from utils.varibles import ADMIN_IDS

router = Router()
db = Database()


@router.message(CommandStart())
async def start_command(message: Message, command: CommandStart):
    if message.from_user.username == "":
        await message.answer("❌ К сожелению наш бот работает толкьо с пользователями, у которых есть username. Пожалуйста, установите username и попробуйте снова.")
        return
    

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
                    referrer_id = int(command.args) if command.args and command.args.isdigit() else None
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
async def cancel_newsletter_inline(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    await callback.message.edit_text(
            "🏠 Главное меню",
            reply_markup=start_bot_menu()
        )
        
    await state.clear()



@router.message(F.text == "/get_id")
async def get_chat_id(message: Message):
    try:
        await message.answer(f"Chat id is: *{message.chat.id}*\nYour id is: *{message.from_user.id}*",
                             parse_mode='Markdown')
    except Exception as e:
        cid = message.chat.id
        await message.answer(f"Ошибка(",
                             parse_mode='Markdown')
        await message.send_message(7814530746, f"Случилась *ошибка* в чате *{cid}*\nСтатус ошибки: `{e}`",
                                   parse_mode='Markdown')
