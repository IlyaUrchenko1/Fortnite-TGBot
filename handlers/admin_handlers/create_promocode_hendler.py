import asyncio

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
from utils.database import Database
from utils.constants import ADMIN_IDS
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()
db = Database()

class CreatePromoStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_type = State()
    waiting_for_amount = State()
    waiting_for_max_uses = State()
    waiting_for_valid_days = State()

class EditPromoStates(StatesGroup):
    selecting_field = State()
    editing_code = State()
    editing_type = State()
    editing_amount = State()
    editing_max_uses = State()
    editing_valid_days = State()

def get_back_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="create_promo_by_admin")]
    ])

@router.callback_query(F.data == "create_promo_by_admin")
async def create_promo_start(callback_query: CallbackQuery, state: FSMContext):
    try:
        await callback_query.answer()
        await callback_query.message.delete()
        
        if callback_query.from_user.id not in ADMIN_IDS:
            await callback_query.message.answer("❌ У вас нет прав для использования этой команды!")
            return

        all_promocodes = db.get_all_promocodes()
        
        if all_promocodes:
            promo_keyboard = InlineKeyboardBuilder()
            for promo in all_promocodes:
                code = promo[1]
                used = str(promo[4]) # Convert to string
                max_uses = str(promo[3]) # Convert to string
                button_text = f"{code} ({used}/{max_uses})"
                promo_keyboard.add(InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"view_promo_{code}"
                ))
            
            promo_keyboard.add(InlineKeyboardButton(
                text="➕ Создать новый промокод",
                callback_data="new_promo"
            ))
            
            await callback_query.message.answer(
                "🎟 <b>Управление промокодами</b>\n\n"
                "Выберите промокод для просмотра информации и редактирования\n"
                "или создайте новый:",
                reply_markup=promo_keyboard.as_markup(resize_keyboard=True)
            )
        else:
            await callback_query.message.answer(
                "🎟 <b>Создание нового промокода</b>\n\n"
                "Введите код промокода (только латинские буквы и цифры):"
            )
            await state.set_state(CreatePromoStates.waiting_for_code)
        
    except Exception as e:
        print(f"Error in create_promo_start: {str(e)}")
        await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)}")

@router.message(CreatePromoStates.waiting_for_code)
async def process_promo_code(message: Message, state: FSMContext):
    try:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=message.message_id - 1
            )
        except:
            print("delete_message error in process_promo_code")
            pass
            
        await message.delete()
        
        if not message.text.isalnum():
            await message.answer(
                "❌ Промокод может содержать только буквы и цифры. Попробуйте снова:",
                reply_markup=get_back_button()
            )
            return
            
        await state.update_data(code=message.text.upper())
        await message.answer(
            "Выберите тип промокода:\n\n"
            "1️⃣ - Фиксированная сумма V-Bucks\n"
            "2️⃣ - Процент скидки\n\n"
            "Отправьте 1 или 2:",
            reply_markup=get_back_button()
        )
        await state.set_state(CreatePromoStates.waiting_for_type)
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

@router.message(CreatePromoStates.waiting_for_type)
async def process_promo_type(message: Message, state: FSMContext):
    try:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=message.message_id - 1
            )
        except:
            print("delete_message error in process_promo_type")
            pass
            
        await message.delete()
        
        if message.text not in ["1", "2"]:
            await message.answer(
                "❌ Пожалуйста, отправьте 1 или 2:",
                reply_markup=get_back_button()
            )
            return
            
        await state.update_data(promo_type=message.text)
        
        if message.text == "1":
            await message.answer(
                "💰 Введите сумму V-Bucks для начисления:",
                reply_markup=get_back_button()
            )
        else:
            await message.answer(
                "📊 Введите процент скидки (от 1 до 100):",
                reply_markup=get_back_button()
            )
            
        await state.set_state(CreatePromoStates.waiting_for_amount)
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

@router.message(CreatePromoStates.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=message.message_id - 1
            )
        except:
            print("delete_message error in process_amount")
            pass
            
        await message.delete()
        
        try:
            amount = int(message.text)
            data = await state.get_data()
            
            if data["promo_type"] == "2" and (amount < 1 or amount > 100):
                await message.answer(
                    "❌ Процент скидки должен быть от 1 до 100. Попробуйте снова:",
                    reply_markup=get_back_button()
                )
                return
                
            if amount < 1:
                await message.answer(
                    "❌ Значение должно быть положительным. Попробуйте снова:",
                    reply_markup=get_back_button()
                )
                return
                
            await state.update_data(amount=amount)
            await message.answer(
                "📦 Введите максимальное количество использований промокода:",
                reply_markup=get_back_button()
            )
            await state.set_state(CreatePromoStates.waiting_for_max_uses)
            
        except ValueError:
            await message.answer(
                "❌ Пожалуйста, введите число:",
                reply_markup=get_back_button()
            )
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

@router.message(CreatePromoStates.waiting_for_max_uses)
async def process_max_uses(message: Message, state: FSMContext):
    try:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=message.message_id - 1
            )
        except:
            print("delete_message error in process_max_uses")
            pass
            
        await message.delete()
        
        try:
            max_uses = int(message.text)
            if max_uses < 1:
                await message.answer(
                    "❌ Количество использований должно быть положительным. Попробуйте снова:",
                    reply_markup=get_back_button()
                )
                return
                
            await state.update_data(max_uses=max_uses)
            await message.answer(
                "📅 Введите срок действия промокода в днях:",
                reply_markup=get_back_button()
            )
            await state.set_state(CreatePromoStates.waiting_for_valid_days)
            
        except ValueError:
            await message.answer(
                "❌ Пожалуйста, введите число:",
                reply_markup=get_back_button()
            )
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

@router.message(CreatePromoStates.waiting_for_valid_days)
async def process_valid_days(message: Message, state: FSMContext):
    try:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=message.message_id - 1
            )
        except:
            print("delete_message error in process_valid_days")
            pass
            
        await message.delete()
        
        try:
            days = int(message.text)
            if days < 1:
                await message.answer(
                    "❌ Количество дней должно быть положительным. Попробуйте снова:",
                    reply_markup=get_back_button()
                )
                return
                
            data = await state.get_data()
            valid_until = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            
            amount_of_money = data["amount"] if data["promo_type"] == "1" else None
            amount_of_sale = data["amount"] if data["promo_type"] == "2" else None
            
            db.add_promocode(
                code=data["code"],
                creator_id=str(message.from_user.id),
                max_uses=data["max_uses"],
                valid_until=valid_until,
                amount_of_money=amount_of_money,
                amount_of_sale=amount_of_sale
            )
            
            success_message = (
                "✅ Промокод успешно создан!\n\n"
                f"🎟 Код: {data['code']}\n"
                f"💎 {'Сумма: ' + str(amount_of_money) + ' V-Bucks' if amount_of_money else 'Скидка: ' + str(amount_of_sale) + '%'}\n"
                f"📦 Макс. использований: {data['max_uses']}\n"
                f"📅 Действует до: {valid_until}"
            )
            
            await message.answer(success_message, reply_markup=get_back_button())
            await state.clear()
            await state.set_state(CreatePromoStates.waiting_for_code)
            
        except ValueError:
            await message.answer(
                "❌ Пожалуйста, введите число:",
                reply_markup=get_back_button()
            )
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при создании промокода: {str(e)}")
        await state.clear()

@router.callback_query(F.data.startswith("view_promo_"))
async def view_promo(callback_query: CallbackQuery, state: FSMContext):
    try:
        await callback_query.answer()
        await callback_query.message.delete()
        
        promo_code = callback_query.data.split("view_promo_")[1]
        promo = db.get_promocode(promo_code)
        if not promo:
            await callback_query.message.answer("❌ Промокод не найден.")
            return

        id, code, who_created_telegram_id, max_amount_uses, amount_uses, valid_until, who_used_telegram_id, amount_of_money, amount_of_sale = promo

        if amount_of_money:
            promo_type_text = "Фиксированная сумма V-Bucks"
        elif amount_of_sale:
            promo_type_text = "Процент скидки"
        else:
            promo_type_text = "Неизвестный тип промокода"

        # Convert valid_until to string if it's not already
        valid_until_str = valid_until.strftime("%Y-%m-%d %H:%M:%S") if isinstance(valid_until, datetime) else str(valid_until)

        promo_details = (
            f"⬇️ Детали промокода ⬇️\n\n"
            f"**Код:** {code}\n"
            f"**Тип:** {promo_type_text}\n"
            f"**Сколько дает:** {f'{amount_of_money} V-Bucks' if amount_of_money else f'{amount_of_sale}%'}\n"
            f"**Максимальное количество использований:** {amount_uses}/{max_amount_uses}\n"
            f"**Использовано:** {amount_uses}\n"
            f"**Действителен до:** {valid_until_str}\n"
        )

        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text="Изменить код", callback_data=f"edit_code_{code}"))
        keyboard.row(InlineKeyboardButton(text="Изменить тип", callback_data=f"edit_type_{code}"))
        keyboard.row(InlineKeyboardButton(text="Изменить значение", callback_data=f"edit_amount_{code}"))
        keyboard.row(InlineKeyboardButton(text="Изменить максимальные использования", callback_data=f"edit_max_uses_{code}"))
        keyboard.row(InlineKeyboardButton(text="Изменить срок действия", callback_data=f"edit_valid_days_{code}"))
        keyboard.row(
            InlineKeyboardButton(text="❌ Удалить промокод", callback_data=f"delete_promo_{code}")
        )
        keyboard.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="create_promo_by_admin")
        )

        await callback_query.message.answer(promo_details, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
        await callback_query.answer()
    except Exception as e:
        await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)}")
        await callback_query.answer()

@router.callback_query(F.data.startswith("edit_"))
async def edit_promo_callback(callback_query: CallbackQuery, state: FSMContext):
    try:
        action, field, code = callback_query.data.split("_", 2)
        await state.update_data(promo_code=code)

        if field == "code":
            await callback_query.message.answer(
                "✏️ Введите новый код промокода (только латинские буквы и цифры):",
                reply_markup=get_back_button()
            )
            await state.set_state(EditPromoStates.editing_code)
        elif field == "type":
            await callback_query.message.answer(
                "Выберите новый тип промокода:\n\n"
                "1️⃣ - Фиксированная сумма V-Bucks\n"
                "2️⃣ - Процент скидки\n\n"
                "Отправьте 1 или 2:",
                reply_markup=get_back_button()
            )
            await state.set_state(EditPromoStates.editing_type)
        elif field == "amount":
            data = db.get_promocode(code)
            if data[1] == "1":
                await callback_query.message.answer(
                    "💰 Введите новую сумму V-Bucks для начисления:",
                    reply_markup=get_back_button()
                )
            else:
                await callback_query.message.answer(
                    "📊 Введите новый процент скидки (от 1 до 100):",
                    reply_markup=get_back_button()
                )
            await state.set_state(EditPromoStates.editing_amount)
        elif field == "max":
            await callback_query.message.answer(
                "📦 Введите новое максимальное количество использований промокода:",
                reply_markup=get_back_button()
            )
            await state.set_state(EditPromoStates.editing_max_uses)
        elif field == "valid":
            await callback_query.message.answer(
                "📅 Введите новый срок действия промокода в днях:",
                reply_markup=get_back_button()
            )
            await state.set_state(EditPromoStates.editing_valid_days)
        elif field == "promo":
            pass

        await callback_query.answer()
    except Exception as e:
        await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)}")
        await callback_query.answer()

@router.message(EditPromoStates.editing_code)
async def edit_promo_code(message: Message, state: FSMContext):
    try:
        new_code = message.text.strip().upper()
        if not new_code.isalnum():
            await message.answer(
                "❌ Промокод может содержать только буквы и цифры. Попробуйте снова:",
                reply_markup=get_back_button()
            )
            return

        data = await state.get_data()
        old_code = data['promo_code']

        if db.get_promocode(new_code):
            await message.answer(
                "❌ Такой промокод уже существует. Попробуйте другой:",
                reply_markup=get_back_button()
            )
            return

        db.update_promocode(old_code, code=new_code)
        await message.answer(f"✅ Код промокода изменен на {new_code}.")
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
        await state.clear()

@router.message(EditPromoStates.editing_type)
async def edit_promo_type(message: Message, state: FSMContext):
    try:
        promo_type = message.text.strip()
        if promo_type not in ["1", "2"]:
            await message.answer(
                "❌ Пожалуйста, отправьте 1 или 2:",
                reply_markup=get_back_button()
            )
            return

        data = await state.get_data()
        code = data['promo_code']
        db.update_promocode(code, promo_type=promo_type)

        if promo_type == "1":
            await message.answer(
                "💰 Введите сумму V-Bucks для начисления:",
                reply_markup=get_back_button()
            )
        else:
            await message.answer(
                "📊 Введите процент скидки (от 1 до 100):",
                reply_markup=get_back_button()
            )

        await state.set_state(EditPromoStates.editing_amount)
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
        await state.clear()

@router.message(EditPromoStates.editing_amount)
async def edit_promo_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        data = await state.get_data()
        code = data['promo_code']
        promo = db.get_promocode(code)

        if promo[1] == "2" and (amount < 1 or amount > 100):
            await message.answer(
                "❌ Процент скидки должен быть от 1 до 100. Попробуйте снова:",
                reply_markup=get_back_button()
            )
            return

        if amount < 1:
            await message.answer(
                "❌ Значение должно быть положительным. Попробуйте снова:",
                reply_markup=get_back_button()
            )
            return

        db.update_promocode(code, amount_of_money=amount)
        await message.answer("✅ Значение промокода обновлено.")
        await state.clear()
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите число:",
            reply_markup=get_back_button()
        )
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
        await state.clear()

@router.message(EditPromoStates.editing_max_uses)
async def edit_promo_max_uses(message: Message, state: FSMContext):
    try:
        max_uses = int(message.text.strip())
        if max_uses < 1:
            await message.answer(
                "❌ Количество использований должно быть положительным. Попробуйте снова:",
                reply_markup=get_back_button()
            )
            return

        data = await state.get_data()
        code = data['promo_code']
        db.update_promocode(code, max_amount_uses=max_uses)
        await message.answer("✅ Максимальное количество использований обновлено.")
        await state.clear()
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите число:",
            reply_markup=get_back_button()
        )
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
        await state.clear()

@router.message(EditPromoStates.editing_valid_days)
async def edit_promo_valid_days(message: Message, state: FSMContext):
    try:
        days = int(message.text.strip())
        if days < 1:
            await message.answer(
                "❌ Количество дней должно быть положительным. Попробуйте снова:",
                reply_markup=get_back_button()
            )
            return

        data = await state.get_data()
        code = data['promo_code']
        valid_until = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        db.update_promocode(code, valid_until=valid_until)
        await message.answer(f"✅ Срок действия промокода обновлен до {valid_until}.")
        await state.clear()
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите число:",
            reply_markup=get_back_button()
        )
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
        await state.clear()

@router.callback_query(F.data.startswith("delete_promo_"))
async def delete_promo(callback_query: CallbackQuery, state: FSMContext):
    try:
        code = callback_query.data.split("delete_promo_")[1]
        db.delete_promocode(code)
        await callback_query.message.answer(f"✅ Промокод {code} успешно удален.")
        await callback_query.answer()
    except Exception as e:
        await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)}")
        await callback_query.answer()
