import json
import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Ваши токены и настройки
TOKEN = os.getenv("BOT_TOKEN")  # Токен берется из переменных окружения Render
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Файл для сохранения данных родкомитета
DATA_FILE = "school_data.json"


def load_data():
  if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  return {
      "1B": {
          "chairman_name": "Алина (Председатель)",
          "chairman_phone": "+996 555 123-456",
          "treasurer_name": "Марат (Казначей)",
          "treasurer_phone": "+996 700 987-654",
      }
  }


def save_data(data):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


# Состояния для изменения данных учителем
class TeacherEdit(StatesGroup):
  waiting_for_chairman_name = State()
  waiting_for_chairman_phone = State()
  waiting_for_treasurer_name = State()
  waiting_for_treasurer_phone = State()


# Главное меню (выбор роли)
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🧑‍🏫 Классный руководитель", callback_data="role_teacher"
              )
          ],
          [InlineKeyboardButton(text="👪 Родителю", callback_data="role_parent")],
      ]
  )
  await message.answer(
      "🏛 **Система безопасности «Школа» (1 «В»)**\n\n"
      "⭐ Единая платформа контроля посещаемости и связи\n\n"
      "Пожалуйста, выберите вашу роль для входа:",
      reply_markup=kb,
      parse_mode="Markdown",
  )


# Меню учителя
@dp.callback_query(F.data == "role_teacher")
async def teacher_menu(callback: types.CallbackQuery):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="⚙️ Изменить контакты родкомитета",
                  callback_data="edit_rodkom",
              )
          ],
          [
              InlineKeyboardButton(
                  text="🔙 На главную", callback_data="back_to_main"
              )
          ],
      ]
  )
  await callback.message.edit_text(
      "🧑‍🏫 **Панель классного руководителя**\n\nВыберите нужное действие:",
      reply_markup=kb,
      parse_mode="Markdown",
  )
  await callback.answer()


# Меню родителя
@dp.callback_query(F.data == "role_parent")
async def parent_menu(callback: types.CallbackQuery):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🟢 Забрать ребенка", callback_data="action_pickup"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🟡 Опоздаем на урок", callback_data="action_late"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🔴 Пропустим / Причина...", callback_data="action_skip"
              )
          ],
          [
              InlineKeyboardButton(
                  text="👥 Родительский комитет (контакты)",
                  callback_data="rodkom_menu",
              )
          ],
          [
              InlineKeyboardButton(
                  text="🔙 На главную", callback_data="back_to_main"
              )
          ],
      ]
  )
  await callback.message.edit_text(
      "👪 **Кабинет родителя (1 «В» класс)**\n\nВыберите нужное действие:",
      reply_markup=kb,
      parse_mode="Markdown",
  )
  await callback.answer()


# Возврат на главную
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🧑‍🏫 Классный руководитель", callback_data="role_teacher"
              )
          ],
          [InlineKeyboardButton(text="👪 Родителю", callback_data="role_parent")],
      ]
  )
  await callback.message.edit_text(
      "🏛 **Система безопасности «Школа» (1 «В»)**\n\n"
      "Пожалуйста, выберите вашу роль для входа:",
      reply_markup=kb,
      parse_mode="Markdown",
  )
  await callback.answer()


# Показ контактов родкомитета родителям
@dp.callback_query(F.data == "rodkom_menu")
async def show_rodkom(callback: types.CallbackQuery):
  data = load_data()
  cls_data = data.get("1B", {})

  text = (
      f"👥 **Родительский комитет (контакты для связи):**\n\n"
      f"• {cls_data.get('chairman_name', 'Не указано')}\n"
      f"📞 Телефон: `{cls_data.get('chairman_phone', '-')}`\n\n"
      f"• {cls_data.get('treasurer_name', 'Не указано')}\n"
      f"📞 Телефон: `{cls_data.get('treasurer_phone', '-')}`\n\n"
      "Нажмите на номер телефона, чтобы скопировать его."
  )

  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="🔙 Назад", callback_data="role_parent")]
      ]
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
  await callback.answer()


# --- Шаги изменения контактов учителем ---
@dp.callback_query(F.data == "edit_rodkom")
async def edit_rodkom_start(callback: types.CallbackQuery, state: FSMContext):
  await callback.message.answer(
      "📝 Введите **ФИО председателя** родительского комитета:"
  )
  await state.set_state(TeacherEdit.waiting_for_chairman_name)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_chairman_name)
async def process_chairman_name(message: types.Message, state: FSMContext):
  await state.update_data(chairman_name=message.text)
  await message.answer("📞 Введите **телефон председателя**:")
  await state.set_state(TeacherEdit.waiting_for_chairman_phone)


@dp.message(TeacherEdit.waiting_for_chairman_phone
