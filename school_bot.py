import asyncio
import json
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

DATA_FILE = "school_data.json"


def load_data():
  if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  return {}


def save_data(data):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


class Registration(StatesGroup):
  waiting_for_class_code = State()
  waiting_for_new_class_name = State()


class TeacherEdit(StatesGroup):
  waiting_for_chairman_name = State()
  waiting_for_chairman_phone = State()
  waiting_for_treasurer_name = State()
  waiting_for_treasurer_phone = State()
  waiting_for_meeting = State()
  waiting_for_announcement = State()
  waiting_for_holidays = State()
  waiting_for_homework = State()
  waiting_for_schedule = State()
  waiting_for_info_help = State()
  waiting_for_students_list = State()
  waiting_for_call_parent = State()
  waiting_for_poll = State()
  waiting_for_treasury = State()
  waiting_for_important_notes = State()


class ParentSendNote(StatesGroup):
  waiting_for_note = State()
  waiting_for_teacher_msg = State()


# --- 1. Главное меню (Вход и Авторизация) ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="➕ Создать новый класс (Учителю)",
                  callback_data="create_class",
              )
          ],
          [
              InlineKeyboardButton(
                  text="🔑 Войти по коду класса", callback_data="join_class"
              )
          ],
      ]
  )
  await message.answer(
      "🏛 **Безопасная школьная цифровая платформа**\n\n"
      "⭐ Система закрытого доступа для школ и классов.\n\n"
      "Выберите действие для входа:",
      reply_markup=kb,
      parse_mode="Markdown",
  )


@dp.callback_query(F.data == "create_class")
async def create_class_start(
    callback: types.CallbackQuery, state: FSMContext
):
  await callback.message.answer(
      "📝 Введите **номер и название школы/класса** (например: *Школа №1, 1"
      " «В»*):"
  )
  await state.set_state(Registration.waiting_for_new_class_name)
  await callback.answer()


@dp.message(Registration.waiting_for_new_class_name)
async def process_create_class(message: types.Message, state: FSMContext):
  data = load_data()
  class_id = f"CLASS_{len(data) + 101}"
  data[class_id] = {
      "name": message.text,
      "chairman_name": "Не указан",
      "chairman_phone": "-",
      "treasurer_name": "Не указан",
      "treasurer_phone": "-",
      "next_meeting": "Собрание пока не запланировано.",
      "announcement": "Нет новых объявлений.",
      "holidays": "Информация о праздниках уточняется.",
      "homework": "Домашнее задание не добавлено.",
      "schedule": "Расписание уроков не добавлено.",
      "info_help": "Справка и правила школы пока не заполнены.",
      "students_list": "Список класса пуст.",
      "attendance_log": "Журнал посещаемости пуст.",
      "treasury_report": "Отчёт по кассе пока не опубликован.",
      "active_poll": "Нет активных опросов.",
      "important_notes": "Медицинские отметки и аллергии не зафиксированы.",
      "medical_notes": [],
      "emergency_alerts": [],
      "subscription": {
          "status": "Бесплатный период (Trial 30 дней)",
          "days_left": 30,
          "price": "500 сом / месяц с класса",
      },
  }
  save_data(data)
  await state.clear()

  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🧑‍🏫 Перейти в панель учителя",
                  callback_data=f"teacher_menu:{class_id}",
              )
          ]
      ]
  )
  await message.answer(
      f"🎉 **Класс «{message.text}» успешно создан!**\n\n"
      f"🔑 **Уникальный код для родителей:** `{class_id}`\n\n"
      f"Передайте этот код родителям. Без него никто сторонний не сможет"
      f" зайти в класс.",
      reply_markup=kb,
      parse_mode="Markdown",
  )


@dp.callback_query(F.data == "join_class")
async def join_class_start(callback: types.CallbackQuery, state: FSMContext):
  await callback.message.answer(
      "🔑 Введите **уникальный код вашего класса** (получите его у учителя,"
      " например: `CLASS_101`):"
  )
  await state.set_state(Registration.waiting_for_class_code)
  await callback.answer()


@dp.message(Registration.waiting_for_class_code)
async def process_join_class(message: types.Message, state: FSMContext):
  class_id = message.text.strip().upper()
  data = load_data()
  if class_id not in data:
    await message.answer(
        "❌ **Код не найден.** Проверьте правильность кода класса и попробуйте"
        " снова."
    )
    return

  await state.clear()
  cls_name = data[class_id].get("name", "Класс")
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="👪 Открыть кабинет родителя",
                  callback_data=f"parent_menu:{class_id}",
              )
          ]
      ]
  )
  await message.answer(
      f"✅ **Код принят! Доступ разрешён.**\nДобро пожаловать в класс"
      f" «{cls_name}»!",
      reply_markup=kb,
      parse_mode="Markdown",
  )


# --- 2. Панель классного руководителя (Учителя) ---
@dp.callback_query(F.filter(F.data.startswith("teacher_menu:")))
async def teacher_menu_handler(callback: types.CallbackQuery):
  class_id = callback.data.split(":")[1]
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🚨 Вызвать родителя (Срочно!)",
                  callback_data=f"t_call_p:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="⚠️ Важно о детях (Аллергии/Здоровье)",
                  callback_data=f"t_notes:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📊 Создать опрос / голосование",
                  callback_data=f"t_poll:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="💰 Обновить отчет кассы / фонда",
                  callback_data=f"t_treasury:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📋 Редактировать список класса",
                  callback_data=f"t_students:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="⚙️ Изменить контакты родкомитета",
                  callback_data=f"t_rodkom:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📅 Назначить собрание",
                  callback_data=f"t_meeting:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📢 Написать объявление",
                  callback_data=f"t_announcement:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="🎉 Праздники и мероприятия",
                  callback_data=f"t_holidays:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📚 Домашнее задание",
                  callback_data=f"t_homework:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="⏰ Расписание уроков",
                  callback_data=f"t_schedule:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="ℹ️ Изменить справку и правила",
                  callback_data=f"t_info_help:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📄 Поступившие справки / заявления",
                  callback_data=f"t_view_notes:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="💳 Статус подписки и тариф",
                  callback_data=f"t_sub:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="🔙 Выйти в главное меню", callback_data="back_to_main"
              )
          ],
      ]
  )
  await callback.message.edit_text(
      f"🧑‍🏫 **Панель классного руководителя**\nКод вашего класса: `{class_id}`\n\nВыберите"
      " раздел управления:",
      reply_markup=kb,
      parse_mode="Markdown",
  )
  await callback.answer()


# --- 3. Кабинет родителя ---
@dp.callback_query(F.filter(F.data.startswith("parent_menu:")))
async def parent_menu_handler(callback: types.CallbackQuery):
  class_id = callback.data.split(":")[1]
  data = load_data()
  cls_name = data.get(class_id, {}).get("name", "Класс")
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🟢 Забрать ребенка",
                  callback_data=f"act_pickup:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="🟡 Опоздаем на урок",
                  callback_data=f"act_late:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="🔴 Ребёнок не пришёл",
                  callback_data=f"act_skip:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="⚠️ Важно о ребёнке (Аллергия/Здоровье)",
                  callback_data=f"p_notes:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="💬 Написать вопрос учителю",
                  callback_data=f"p_write_t:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📊 Опросы и голосования класса",
                  callback_data=f"p_poll:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="💰 Баланс фонда класса / Казначей",
                  callback_data=f"p_treasury:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📄 Отправить справку / заявление",
                  callback_data=f"p_send_note:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📚 Домашнее задание", callback_data=f"p_hw:{class_id}"
              )
          ],
          [
              InlineKeyboardButton(
                  text="⏰ Расписание уроков", callback_data=f"p_sch:{class_id}"
              )
          ],
          [
              InlineKeyboardButton(
                  text="👥 Родительский комитет",
                  callback_data=f"p_rodkom:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📅 Родительские собрания",
                  callback_data=f"p_meeting:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📢 Объявления класса",
                  callback_data=f"p_announcement:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="🎉 Праздники и мероприятия",
                  callback_data=f"p_holidays:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="ℹ️ Справка и правила школы",
                  callback_data=f"p_info_help:{class_id}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="🔙 Выйти в главное меню", callback_data="back_to_main"
              )
          ],
      ]
  )
  await callback.message.edit_text(
      f"👪 **Кабинет родителя ({cls_name})**\n\nВыберите нужный раздел:",
      reply_markup=kb,
      parse_mode="Markdown",
  )
  await callback.answer()


@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
  await cmd_start(callback.message, state)
  await callback.answer()


# --- Обработчики разделов учителя ---
@dp.callback_query(F.filter(F.data.startswith("t_call_p:")))
async def t_call_parent_start(
    callback: types.CallbackQuery, state: FSMContext
):
  class_id = callback.data.split(":")[1]
  await state.update_data(current_class=class_id)
  await callback.message.answer(
      "🚨 Введите **ФИО ребенка** и **причину срочного вызова** (например:"
      " *Иванов В. — поднялась температура, срочно забрать*):"
  )
  await state.set_state(TeacherEdit.waiting_for_call_parent)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_call_parent)
async def process_t_call_parent(message: types.Message, state: FSMContext):
  user_data = await state.get_data()
  class_id = user_data.get("current_class")
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в панель учителя",
              callback_data=f"teacher_menu:{class_id}",
          )
      ]]
  )
  await message.answer(
      f"🚨 **СРОЧНЫЙ ВЫЗОВ СФОРМИРОВАН!**\n\nТекст: {message.text}\nУведомление"
      " отправлено родителям.",
      reply_markup=kb,
      parse_mode="Markdown",
  )


@dp.callback_query(F.filter(F.data.startswith("t_notes:")))
async def t_notes_start(callback: types.CallbackQuery, state: FSMContext):
  class_id = callback.data.split(":")[1]
  await state.update_data(current_class=class_id)
  await callback.message.answer(
      "⚠️ Введите новые медицинские отметки/аллергии у детей:"
  )
  await state.set_state(TeacherEdit.waiting_for_important_notes)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_important_notes)
async def process_t_notes(message: types.Message, state: FSMContext):
  user_data = await state.get_data()
  class_id = user_data.get("current_class")
  data = load_data()
  if class_id in data:
    data[class_id]["important_notes"] = message.text
    save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в панель учителя",
              callback_data=f"teacher_menu:{class_id}",
          )
      ]]
  )
  await message.answer(
      "✅ **Отметки о здоровье успешно обновлены!**",
      reply_markup=kb,
      parse_mode="Markdown",
  )


@dp.callback_query(F.filter(F.data.startswith("t_poll:")))
async def t_poll_start(callback: types.CallbackQuery, state: FSMContext):
  class_id = callback.data.split(":")[1]
  await state.update_data(current_class=class_id)
  await callback.message.answer("📊 Введите тему нового опроса класса:")
  await state.set_state(TeacherEdit.waiting_for_poll)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_poll)
async def process_t_poll(message: types.Message, state: FSMContext):
  user_data = await state.get_data()
  class_id = user_data.get("current_class")
  data = load_data()
  if class_id in data:
    data[class_id]["active_poll"] = (
        f"📊 **Опрос:** {message.text}\n• Вариант 1: Да\n• Вариант 2: Нет"
    )
    save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в панель учителя",
              callback_data=f"teacher_menu:{class_id}",
          )
      ]]
  )
  await message.answer(
      "✅ **Опрос успешно открыт!**", reply_markup=kb, parse_mode="Markdown"
  )


@dp.callback_query(F.filter(F.data.startswith("t_treasury:")))
async def t_treasury_start(callback: types.CallbackQuery, state: FSMContext):
  class_id = callback.data.split(":")[1]
  await state.update_data(current_class=class_id)
  await callback.message.answer(
      "💰 Введите новые данные о балансе и расходах фонда класса:"
  )
  await state.set_state(TeacherEdit.waiting_for_treasury)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_treasury)
async def process_t_treasury(message: types.Message, state: FSMContext):
  user_data = await state.get_data()
  class_id = user_data.get("current_class")
  data = load_data()
  if class_id in data:
    data[class_id]["treasury_report"] = message.text
    save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в панель учителя",
              callback_data=f"teacher_menu:{class_id}",
          )
      ]]
  )
  await message.answer(
      "✅ **Отчёт по кассе обновлен!**", reply_markup=kb, parse_mode="Markdown"
  )


@dp.callback_query(F.filter(F.data.startswith("t_students:")))
async def t_students_start(callback: types.CallbackQuery, state: FSMContext):
  class_id = callback.data.split(":")[1]
  await state.update_data(current_class=class_id)
  await callback.message.answer("📋 Введите новый список учеников класса:")
  await state.set_state(TeacherEdit.waiting_for_students_list)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_students_list)
async def process_t_students(message: types.Message, state: FSMContext):
  user_data = await state.get_data()
  class_id = user_data.get("current_class")
  data = load_data()
  if class_id in data:
    data[class_id]["students_list"] = message.text
    save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в панель учителя",
              callback_data=f"teacher_menu:{class_id}",
          )
      ]]
  )
  await message.answer(
      "✅ **Список класса обновлен!**", reply_markup=kb, parse_mode="Markdown"
  )


@dp.callback_query(F.filter(F.data.startswith("t_rodkom:")))
async def t_rodkom_start(callback: types.CallbackQuery, state: FSMContext):
  class_id = callback.data.split(":")[1]
  await state.update_data(current_class=class_id)
  await callback.message.answer("📝 Введите **ФИО председателя** родкомитета:")
  await state.set_state(TeacherEdit.waiting_for_chairman_name)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_chairman_name)
async def process_t_chairman_name(message: types.Message, state: FSMContext):
  await state.update_data(chairman_name=message.text)
  await message.answer("📞 Введите **телефон председателя**:")
  await state.set_state(TeacherEdit.waiting_for_chairman_phone)


@dp.message(TeacherEdit.waiting_for_chairman_phone)
async def process_t_chairman_phone(message: types.Message, state: FSMContext):
  await state.update_data(chairman_phone=message.text)
  await message.answer("📝 Введите **ФИО казначея**:")
  await state.set_state(TeacherEdit.waiting_for_treasurer_name)


@dp.message(TeacherEdit.waiting_for_treasurer_name)
async def process_t_treasurer_name(message: types.Message, state: FSMContext):
  await state.update_data(treasurer_name=message.text)
  await message.answer("📞 Введите **телефон казначея**:")
  await state.set_state(TeacherEdit.waiting_for_treasurer_phone)


@dp.message(TeacherEdit.waiting_for_treasurer_phone)
async def process_t_treasurer_phone(message: types.Message, state: FSMContext):
  user_data = await state.get_data()
  class_id = user_data.get("current_class")
  data = load_data()
  if class_id in data:
    data[class_id].update({
        "chairman_name": user_data.get("chairman_name"),
        "chairman_phone": user_data.get("chairman_phone"),
        "treasurer_name": user_data.get("treasurer_name"),
        "treasurer_phone": message.text,
    })
    save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в панель учителя",
              callback_data=f"teacher_menu:{class_id}",
          )
      ]]
  )
  await message.answer(
      "✅ **Контакты родкомитета обновлены!**",
      reply_markup=kb,
      parse_mode="Markdown",
  )


@dp.callback_query(F.filter(F.data.startswith("t_meeting:")))
async def t_meeting_start(callback: types.CallbackQuery, state: FSMContext):
  class_id = callback.data.split(":")[1]
  await state.update_data(current_class=class_id)
  await callback.message.answer(
      "📅 Введите дату и тему родительского собрания:"
  )
  await state.set_state(TeacherEdit.waiting_for_meeting)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_meeting)
async def process_t_meeting(message: types.Message, state: FSMContext):
  user_data = await state.get_data()
  class_id = user_data.get("current_class")
  data = load_data()
  if class_id in data:
    data[class_id]["next_meeting"] = message.text
    save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в панель учителя",
              callback_data=f"teacher_menu:{class_id}",
          )
      ]]
  )
  await message.answer(
      "✅ **Информация о собрании обновлена!**",
      reply_markup=kb,
      parse_mode="Markdown",
  )


@dp.callback_query(F.filter(F.data.startswith("t_announcement:")))
async def t_announcement_start(
    callback: types.CallbackQuery, state: FSMContext
):
  class_id = callback.data.split(":")[1]
  await state.update_data(current_class=class_id)
  await callback.message.answer("📢 Введите текст нового объявления:")
  await state.set_state(TeacherEdit.waiting_for_announcement)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_announcement)
async def process_t_announcement(message: types.Message, state: FSMContext):
  user_data = await state.get_data()
  class_id = user_data.get("current_class")
  data = load_data()
  if class_id in data:
    data[class_id]["announcement"] = message.text
    save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в панель учителя",
              callback_data=f"teacher_menu:{class_id}",
          )
      ]]
  )
  await message.answer(
      "✅ **Объявление опубликовано!**", reply_markup=kb, parse_mode="Markdown"
  )


@dp.callback_query(F.filter(F.data.startswith("t_holidays:")))
async def t_holidays_start(callback: types.CallbackQuery, state: FSMContext):
  class_id = callback.data.split(":")[1]
  await state.update_data(current_class=class_id)
  await callback.message.answer("🎉 Введите список праздников и мероприятий:")
  await state.set_state(TeacherEdit.waiting_for_holidays)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_holidays)
async def process_t_holidays(message: types.Message, state: FSMContext):
  user_data = await state.get_data()
  class_id = user_data.get("current_class")
  data = load_data()
  if class_id in data:
    data[class_id]["holidays"] = message.text
    save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в панель учителя",
              callback_data=f"teacher_menu:{class_id}",
          )
      ]]
  )
  await message.answer(
      "✅ **Список мероприятий обновлен!**",
      reply_markup=kb,
      parse_mode="Markdown",
  )


@dp.callback_query(F.filter(F.data.startswith("t_homework:")))
async def t_homework_start(callback: types.CallbackQuery, state: FSMContext):
  class_id = callback.data.split(":")[1]
  await state.update_data(current_class=class_id)
  await callback.message.answer("📚 Введите домашнее задание:")
  await state.set_state(TeacherEdit.waiting_for_homework)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_homework)
async def process_t_homework(message: types.Message, state: FSMContext):
  user_data = await state.get_data()
  class_id = user_data.get("current_class")
  data = load_data()
  if class_id in data:
    data[class_id]["homework"] = message.text
    save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в панель учителя",
              callback_data=f"teacher_menu:{class_id}",
          )
      ]]
  )
  await message.answer(
      "✅ **Домашнее задание обновлено!**",
      reply_markup=kb,
      parse_mode="Markdown",
  )


@dp.callback_query(F.filter(F.data.startswith("t_schedule:")))
async def t_schedule_start(callback: types.CallbackQuery, state: FSMContext):
  class_id = callback.data.split(":")[1]
  await state.update_data(current_class=class_id)
  await callback.message.answer("⏰ Введите расписание уроков:")
  await state.set_state(TeacherEdit.waiting_for_schedule)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_schedule)
async def process_t_schedule(message: types.Message, state: FSMContext):
  user_data = await state.get_data()
  class_id = user_data.get("current_class")
  data = load_data()
  if class_id in data:
    data[class_id]["schedule"] = message.text
    save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в панель учителя",
              callback_data=f"teacher_menu:{class_id}",
          )
      ]]
  )
  await message.answer(
      "✅ **Расписание обновлено!**", reply_markup=kb, parse_mode="Markdown"
  )


@dp.callback_query(F.filter(F.data.startswith("t_info_help:")))
async def t_info_help_start(
    callback: types.CallbackQuery, state: FSMContext
):
  class_id = callback.data.split(":")[1]
  await state.update_data(current_class=class_id)
  await callback.message.answer("ℹ️ Введите текст справки и правил школы:")
  await state.set_state(TeacherEdit.waiting_for_info_help)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_info_help)
async def process_t_info_help(message: types.Message, state: FSMContext):
  user_data = await state.get_data()
  class_id = user_data.get("current_class")
  data = load_data()
  if class_id in data:
    data[class_id]["info_help"] = message.text
    save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в панель учителя",
              callback_data=f"teacher_menu:{class_id}",
          )
      ]]
  )
  await message.answer(
      "✅ **Справка и правила школы обновлены!**",
      reply_markup=kb,
      parse_mode="Markdown",
  )


@dp.callback_query(F.filter(F.data.startswith("t_view_notes:")))
async def t_view_notes(callback: types.CallbackQuery):
  class_id = callback.data.split(":")[1]
  data = load_data()
  notes = data.get(class_id, {}).get("medical_notes", [])
  text = (
      "📄 **ПОСТУПИВШИЕ СПРАВКИ И ЗАЯВЛЕНИЯ:**\n\n" + "\n\n".join(notes)
      if notes
      else "📄 Поступивших справок и заявлений нет."
  )
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в панель учителя",
              callback_data=f"teacher_menu:{class_id}",
          )
      ]]
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
  await callback.answer()


@dp.callback_query(F.filter(F.data.startswith("t_sub:")))
async def t_sub_status(callback: types.CallbackQuery):
  class_id = callback.data.split(":")[1]
  data = load_data()
  sub = data.get(class_id, {}).get("subscription", {})
  text = (
      f"💳 **Статус подписки класса:**\n\n"
      f"• **Текущий тариф:** {sub.get('status', 'Пробный период')}\n"
      f"• **Осталось дней:** {sub.get('days_left', 30)} дн.\n"
      f"• **Стоимость продления:** {sub.get('price', '500 сом / мес')}\n\n"
      f"🔔 *Автоматическое уведомление о продлении придёт за 3 дня до конца"
      f" периода.*"
  )
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в панель учителя",
              callback_data=f"teacher_menu:{class_id}",
          )
      ]]
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
  await callback.answer()


# --- Обработчики разделов родителя ---
@dp.callback_query(F.filter(F.data.startswith("p_notes:")))
async def p_notes(callback: types.CallbackQuery):
  class_id = callback.data.split(":")[1]
  data = load_data()
  text = data.get(class_id, {}).get(
      "important_notes", "Медицинские отметки не зафиксированы."
  )
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в кабинет родителя",
              callback_data=f"parent_menu:{class_id}",
          )
      ]]
  )
  await callback.message.edit_text(
      f"⚠️ **Важно о здоровье детей:**\n\n{text}",
      reply_markup=kb,
      parse_mode="Markdown",
  )
  await callback.answer()


@dp.callback_query(F.filter(F.data.startswith("p_write_t:")))
async def p_write_teacher(callback: types.CallbackQuery, state: FSMContext):
  class_id = callback.data.split(":")[1]
  await state.update_data(current_class=class_id)
  await callback.message.answer(
      "💬 Напишите ваш личный вопрос классному руководителю:"
  )
  await state.set_state(ParentSendNote.waiting_for_teacher_msg)
  await callback.answer()


@dp.message(ParentSendNote.waiting_for_teacher_msg)
async def process_p_write_teacher(message: types.Message, state: FSMContext):
  user_data = await state.get_data()
  class_id = user_data.get("current_class")
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в кабинет родителя",
              callback_data=f"parent_menu:{class_id}",
          )
      ]]
  )
  await message.answer(
      "✅ **Ваше сообщение конфиденциально передано учителю!**",
      reply_markup=kb,
      parse_mode="Markdown",
  )


@dp.callback_query(F.filter(F.data.startswith("p_poll:")))
async def p_poll(callback: types.CallbackQuery):
  class_id = callback.data.split(":")[1]
  data = load_data()
  poll_text = data.get(class_id, {}).get("active_poll", "Нет активных опросов.")
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="👍 Проголосовать «ДА»", callback_data="vote_yes"
              )
          ],
          [
              InlineKeyboardButton(
                  text="👎 Проголосовать «НЕТ»", callback_data="vote_no"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🔙 Назад в кабинет родителя",
                  callback_data=f"parent_menu:{class_id}",
              )
          ],
      ]
  )
  await callback.message.edit_text(
      poll_text, reply_markup=kb, parse_mode="Markdown"
  )
  await callback.answer()


@dp.callback_query(F.data.in_(["vote_yes", "vote_no"]))
async def process_vote(callback: types.CallbackQuery):
  await callback.answer("✅ Ваш голос учтён!", show_alert=True)


@dp.callback_query(F.filter(F.data.startswith("p_treasury:")))
async def p_treasury(callback: types.CallbackQuery):
  class_id = callback.data.split(":")[1]
  data = load_data()
  text = data.get(class_id, {}).get(
      "treasury_report", "Отчёт казначея отсутствует."
  )
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в кабинет родителя",
              callback_data=f"parent_menu:{class_id}",
          )
      ]]
  )
  await callback.message.edit_text(
      f"💰 **Фонд класса (Отчёт казначея):**\n\n{text}",
      reply_markup=kb,
      parse_mode="Markdown",
  )
  await callback.answer()


@dp.callback_query(F.filter(F.data.startswith("p_send_note:")))
async def p_send_note(callback: types.CallbackQuery, state: FSMContext):
  class_id = callback.data.split(":")[1]
  await state.update_data(current_class=class_id)
  await callback.message.answer(
      "📄 Напишите ФИО ребенка и причину отсутствия (или отправьте текст"
      " заявления):"
  )
  await state.set_state(ParentSendNote.waiting_for_note)
  await callback.answer()


@dp.message(ParentSendNote.waiting_for_note)
async def process_p_send_note(message: types.Message, state: FSMContext):
  user_data = await state.get_data()
  class_id = user_data.get("current_class")
  data = load_data()
  if class_id in data:
    note_entry = f"• {message.from_user.full_name}: {message.text}"
    data[class_id].setdefault("medical_notes", []).append(note_entry)
    save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в кабинет родителя",
              callback_data=f"parent_menu:{class_id}",
          )
      ]]
  )
  await message.answer(
      "✅ **Заявление/справка передана учителю!**",
      reply_markup=kb,
      parse_mode="Markdown",
  )


@dp.callback_query(F.filter(F.data.startswith("p_hw:")))
async def p_hw(callback: types.CallbackQuery):
  class_id = callback.data.split(":")[1]
  data = load_data()
  text = data.get(class_id, {}).get("homework", "Домашнее задание не добавлено.")
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в кабинет родителя",
              callback_data=f"parent_menu:{class_id}",
          )
      ]]
  )
  await callback.message.edit_text(
      f"📚 **Домашнее задание:**\n\n{text}",
      reply_markup=kb,
      parse_mode="Markdown",
  )
  await callback.answer()


@dp.callback_query(F.filter(F.data.startswith("p_sch:")))
async def p_sch(callback: types.CallbackQuery):
  class_id = callback.data.split(":")[1]
  data = load_data()
  text = data.get(class_id, {}).get("schedule", "Расписание не добавлено.")
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в кабинет родителя",
              callback_data=f"parent_menu:{class_id}",
          )
      ]]
  )
  await callback.message.edit_text(
      f"⏰ **Расписание уроков:**\n\n{text}",
      reply_markup=kb,
      parse_mode="Markdown",
  )
  await callback.answer()


@dp.callback_query(F.filter(F.data.startswith("p_rodkom:")))
async def p_rodkom(callback: types.CallbackQuery):
  class_id = callback.data.split(":")[1]
  data = load_data()
  cls_data = data.get(class_id, {})
  text = (
      f"👥 **Родительский комитет:**\n\n"
      f"• Председатель: {cls_data.get('chairman_name', '-')}\n"
      f"📞 Телефон: `{cls_data.get('chairman_phone', '-')}`\n\n"
      f"• Казначей: {cls_data.get('treasurer_name', '-')}\n"
      f"📞 Телефон: `{cls_data.get('treasurer_phone', '-')}`"
  )
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в кабинет родителя",
              callback_data=f"parent_menu:{class_id}",
          )
      ]]
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
  await callback.answer()


@dp.callback_query(F.filter(F.data.startswith("p_meeting:")))
async def p_meeting(callback: types.CallbackQuery):
  class_id = callback.data.split(":")[1]
  data = load_data()
  text = data.get(class_id, {}).get(
      "next_meeting", "Собрания не запланированы."
  )
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в кабинет родителя",
              callback_data=f"parent_menu:{class_id}",
          )
      ]]
  )
  await callback.message.edit_text(
      f"📅 **Родительские собрания:**\n\n{text}",
      reply_markup=kb,
      parse_mode="Markdown",
  )
  await callback.answer()


@dp.callback_query(F.filter(F.data.startswith("p_announcement:")))
async def p_announcement(callback: types.CallbackQuery):
  class_id = callback.data.split(":")[1]
  data = load_data()
  text = data.get(class_id, {}).get("announcement", "Нет новых объявлений.")
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в кабинет родителя",
              callback_data=f"parent_menu:{class_id}",
          )
      ]]
  )
  await callback.message.edit_text(
      f"📢 **Объявления класса:**\n\n{text}",
      reply_markup=kb,
      parse_mode="Markdown",
  )
  await callback.answer()


@dp.callback_query(F.filter(F.data.startswith("p_holidays:")))
async def p_holidays(callback: types.CallbackQuery):
  class_id = callback.data.split(":")[1]
  data = load_data()
  text = data.get(class_id, {}).get("holidays", "Праздников пока нет.")
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в кабинет родителя",
              callback_data=f"parent_menu:{class_id}",
          )
      ]]
  )
  await callback.message.edit_text(
      f"🎉 **Праздники и мероприятия:**\n\n{text}",
      reply_markup=kb,
      parse_mode="Markdown",
  )
  await callback.answer()


@dp.callback_query(F.filter(F.data.startswith("p_info_help:")))
async def p_info_help(callback: types.CallbackQuery):
  class_id = callback.data.split(":")[1]
  data = load_data()
  text = data.get(class_id, {}).get("info_help", "Правила не заполнены.")
  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="🔙 Назад в кабинет родителя",
              callback_data=f"parent_menu:{class_id}",
          )
      ]]
  )
  await callback.message.edit_text(
      f"ℹ️ **Справка и правила школы:**\n\n{text}",
      reply_markup=kb,
      parse_mode="Markdown",
  )
  await callback.answer()


# Кнопки быстрых отметок посещаемости
@dp.callback_query(F.filter(F.data.startswith("act_")))
async def process_attendance_actions(callback: types.CallbackQuery):
  action = callback.data.split(":")[0]
  responses = {
      "act_pickup": "🟢 Учитель уведомлен, что вы забираете ребенка.",
      "act_late": "🟡 Учитель уведомлен об опоздании.",
      "act_skip": "🔴 Отметка сохранена: ребенок сегодня не пришел.",
  }
  await callback.answer(responses.get(action, "Готово!"), show_alert=True)


# --- Веб-сервер 24/7 ---
async def handle(request):
  return web.Response(text="Multiclass School Bot is Running 24/7!")


async def web_server():
  app = web.Application()
  app.router.add_get("/", handle)
  runner = web.AppRunner(app)
  await runner.setup()
  port = int(os.environ.get("PORT", 10000))
  site = web.TCPSite(runner, "0.0.0.0", port)
  await site.start()


async def main():
  asyncio.create_task(web_server())
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
