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
  return {
      "1B": {
          "chairman_name": "Алина (Председатель)",
          "chairman_phone": "+996 555 123-456",
          "treasurer_name": "Марат (Казначей)",
          "treasurer_phone": "+996 700 987-654",
          "next_meeting": (
              "📅 Пятница, 18:00 — Собрание по поводу поездки в музей"
          ),
          "announcement": "Уважаемые родители! Форма одежды на следующую неделю парадная.",
          "holidays": (
              "🎉 Ближайшие праздники и мероприятия:\n- 10 ноября: День"
              " осенних поделок\n- 20 ноября: Праздник букваря"
          ),
          "homework": (
              "📚 Домашнее задание на завтра:\n- Математика: стр. 15, № 3\n-"
              " Русский язык: упр. 24\n- Чтение: стр. 40-42"
          ),
          "schedule": (
              "⏰ Расписание уроков (1 «В»):\n1. Математика\n2. Русский"
              " язык\n3. Чтение\n4. Окружающий мир\n5. ИЗО"
          ),
          "info_help": (
              "ℹ️ **Школьная справка и правила:**\n\n🏫 Школа №1\n📞 Вахта /"
              " Охрана: +996 312 000-000\n👩‍⚕️ Медкабинет: Пн-Пт 8:00 - 16:00\n\n📌"
              " **Правила:** При пропуске более 3 дней требуется медицинская"
              " справка!"
          ),
          "students_list": (
              "📋 **Список класса (1 «В»):**\n1. Абдыкадыров А. ⚠️ (Аллергия на"
              " орехи)\n2. Асанов Б.\n3. Бекболотова Д. 🔴 (Аллергия на лактозу)\n4."
              " Иванов В.\n5. Исмаилова А."
          ),
          "attendance_log": (
              "📊 **Журнал посещаемости на сегодня:**\n• Присутствуют: 22\n•"
              " Опоздают: 1\n• Не пришёл: 2"
          ),
          "treasury_report": (
              "💰 **Фонд класса (Отчёт казначея):**\n• Баланс: 4,500 сом\n• Последние"
              " расходы: Покупка рабочей тетради и антисептиков"
          ),
          "active_poll": (
              "📊 **Активный опрос класса:**\nТема: Поездка в музей в"
              " субботу\n• Вариант 1: Да, едем (18 голосов)\n• Вариант 2: Нет (3"
              " голоса)"
          ),
          "important_notes": (
              "⚠️ **ВАЖНО О ДЕТЯХ (Аллергии и медицинские отметки):**\n•"
              " Абдыкадыров А. — Аллергия на арахис и орехи!\n• Бекболотова Д. —"
              " Аллергия на цитрусовые и лактозу!"
          ),
          "subscription": {
              "status": "Бесплатный период (Trial)",
              "days_left": 30,
              "price": "500 сом / месяц с класса",
          },
      }
  }


def save_data(data):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


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


# --- 1. Главное меню ---
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
      "🏛 **Школьная цифровая платформа (1 «В» класс)**\n\n"
      "⭐ Единый центр связи, безопасности, посещаемости и фонда класса\n\n"
      "Пожалуйста, выберите вашу роль:",
      reply_markup=kb,
      parse_mode="Markdown",
  )


# --- 2. Панель классного руководителя ---
@dp.callback_query(F.data == "role_teacher")
async def teacher_menu(callback: types.CallbackQuery):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🚨 Вызвать родителя (Срочно!)",
                  callback_data="teacher_call_parent_start",
              )
          ],
          [
              InlineKeyboardButton(
                  text="⚠️ Важно о детях (Аллергии/Здоровье)",
                  callback_data="edit_important_notes",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📊 Создать опрос / голосование",
                  callback_data="edit_poll",
              )
          ],
          [
              InlineKeyboardButton(
                  text="💰 Обновить отчет кассы / фонда",
                  callback_data="edit_treasury",
              )
          ],
          [
              InlineKeyboardButton(
                  text="⚙️ Изменить контакты родкомитета",
                  callback_data="edit_rodkom",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📅 Назначить собрание", callback_data="edit_meeting"
              )
          ],
          [
              InlineKeyboardButton(
                  text="📢 Написать объявление",
                  callback_data="edit_announcement",
              )
          ],
          [
              InlineKeyboardButton(
                  text="🎉 Праздники и мероприятия",
                  callback_data="edit_holidays",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📚 Домашнее задание", callback_data="edit_homework"
              )
          ],
          [
              InlineKeyboardButton(
                  text="⏰ Расписание уроков", callback_data="edit_schedule"
              )
          ],
          [
              InlineKeyboardButton(
                  text="ℹ️ Изменить справку и правила",
                  callback_data="edit_info_help",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📋 Список класса и журнал",
                  callback_data="teacher_students_view",
              )
          ],
          [
              InlineKeyboardButton(
                  text="💳 Статус подписки и тариф",
                  callback_data="teacher_sub_status",
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
      "🧑‍🏫 **Панель классного руководителя**\n\nВыберите раздел управления:",
      reply_markup=kb,
      parse_mode="Markdown",
  )
  await callback.answer()


# --- 3. Кабинет родителя ---
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
                  text="🔴 Ребёнок не пришёл", callback_data="action_skip"
              )
          ],
          [
              InlineKeyboardButton(
                  text="⚠️ Важно о ребёнке (Аллергия/Здоровье)",
                  callback_data="parent_view_important",
              )
          ],
          [
              InlineKeyboardButton(
                  text="💬 Написать вопрос учителю",
                  callback_data="parent_write_teacher",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📊 Опросы и голосования класса",
                  callback_data="parent_view_poll",
              )
          ],
          [
              InlineKeyboardButton(
                  text="💰 Баланс фонда класса / Казначей",
                  callback_data="parent_view_treasury",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📄 Отправить справку / заявление",
                  callback_data="send_medical_note",
              )
          ],
          [
              InlineKeyboardButton(
                  text="📚 Домашнее задание", callback_data="parent_homework"
              )
          ],
          [
              InlineKeyboardButton(
                  text="⏰ Расписание уроков", callback_data="parent_schedule"
              )
          ],
          [
              InlineKeyboardButton(
                  text="👥 Родительский комитет", callback_data="rodkom_menu"
              )
          ],
          [
              InlineKeyboardButton(
                  text="📅 Родительские собрания", callback_data="parent_meetings"
              )
          ],
          [
              InlineKeyboardButton(
                  text="📢 Объявления класса", callback_data="parent_announcements"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🎉 Праздники и мероприятия",
                  callback_data="parent_holidays",
              )
          ],
          [
              InlineKeyboardButton(
                  text="ℹ️ Справка и правила школы",
                  callback_data="parent_info_help",
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
      "👪 **Кабинет родителя (1 «В» класс)**\n\nВыберите нужный раздел:",
      reply_markup=kb,
      parse_mode="Markdown",
  )
  await callback.answer()


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
      "🏛 **Школьная цифровая платформа (1 «В» класс)**\n\n"
      "Пожалуйста, выберите вашу роль:",
      reply_markup=kb,
      parse_mode="Markdown",
  )
  await callback.answer()


# --- Просмотры для родителей ---
@dp.callback_query(F.data == "parent_view_important")
async def parent_view_important(callback: types.CallbackQuery):
  data = load_data()
  cls_data = data.get("1B", {})
  text = cls_data.get(
      "important_notes", "Отметки об аллергиях не зафиксированы."
  )
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="🔙 Назад", callback_data="role_parent")]
      ]
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
  await callback.answer()


@dp.callback_query(F.data == "parent_view_poll")
async def parent_view_poll(callback: types.CallbackQuery):
  data = load_data()
  cls_data = data.get("1B", {})
  text = cls_data.get("active_poll", "Нет активных опросов.")
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
          [InlineKeyboardButton(text="🔙 Назад", callback_data="role_parent")],
      ]
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
  await callback.answer()


@dp.callback_query(F.data.in_(["vote_yes", "vote_no"]))
async def process_vote(callback: types.CallbackQuery):
  await callback.answer("✅ Ваш голос учтён!", show_alert=True)


@dp.callback_query(F.data == "parent_view_treasury")
async def parent_view_treasury(callback: types.CallbackQuery):
  data = load_data()
  cls_data = data.get("1B", {})
  text = cls_data.get("treasury_report", "Отчёт по кассе отсутствует.")
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="🔙 Назад", callback_data="role_parent")]
      ]
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
  await callback.answer()


@dp.callback_query(F.data == "parent_write_teacher")
async def parent_write_teacher_start(
    callback: types.CallbackQuery, state: FSMContext
):
  await callback.message.answer(
      "💬 Напишите ваше сообщение / вопрос классному руководителю:"
  )
  await state.set_state(ParentSendNote.waiting_for_teacher_msg)
  await callback.answer()


@dp.message(ParentSendNote.waiting_for_teacher_msg)
async def process_teacher_msg(message: types.Message, state: FSMContext):
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔙 В кабинет родителя", callback_data="role_parent"
              )
          ]
      ]
  )
  await message.answer(
      "✅ **Ваше сообщение передано классному руководителю!**",
      reply_markup=kb,
      parse_mode="Markdown",
  )


# --- Стандартные разделы просмотра ---
@dp.callback_query(F.data == "rodkom_menu")
async def show_rodkom(callback: types.CallbackQuery):
  data = load_data()
  cls_data = data.get("1B", {})
  text = (
      f"👥 **Родительский комитет (контакты):**\n\n"
      f"• {cls_data.get('chairman_name', 'Не указано')}\n"
      f"📞 Телефон: `{cls_data.get('chairman_phone', '-')}`\n\n"
      f"• {cls_data.get('treasurer_name', 'Не указано')}\n"
      f"📞 Телефон: `{cls_data.get('treasurer_phone', '-')}`"
  )
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="🔙 Назад", callback_data="role_parent")]
      ]
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
  await callback.answer()


@dp.callback_query(F.data == "parent_meetings")
async def show_meetings(callback: types.CallbackQuery):
  data = load_data()
  cls_data = data.get("1B", {})
  text = f"📅 **Родительские собрания:**\n\n{cls_data.get('next_meeting', '-')}"
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="🔙 Назад", callback_data="role_parent")]
      ]
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
  await callback.answer()


@dp.callback_query(F.data == "parent_announcements")
async def show_announcements(callback: types.CallbackQuery):
  data = load_data()
  cls_data = data.get("1B", {})
  text = f"📢 **Объявления класса:**\n\n{cls_data.get('announcement', '-')}"
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="🔙 Назад", callback_data="role_parent")]
      ]
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
  await callback.answer()


@dp.callback_query(F.data == "parent_holidays")
async def show_holidays(callback: types.CallbackQuery):
  data = load_data()
  cls_data = data.get("1B", {})
  text = f"🎉 **Праздники и мероприятия:**\n\n{cls_data.get('holidays', '-')}"
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="🔙 Назад", callback_data="role_parent")]
      ]
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
  await callback.answer()


@dp.callback_query(F.data == "parent_homework")
async def show_homework(callback: types.CallbackQuery):
  data = load_data()
  cls_data = data.get("1B", {})
  text = f"📚 **Домашнее задание:**\n\n{cls_data.get('homework', '-')}"
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="🔙 Назад", callback_data="role_parent")]
      ]
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
  await callback.answer()


@dp.callback_query(F.data == "parent_schedule")
async def show_schedule(callback: types.CallbackQuery):
  data = load_data()
  cls_data = data.get("1B", {})
  text = f"⏰ **Расписание уроков:**\n\n{cls_data.get('schedule', '-')}"
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="🔙 Назад", callback_data="role_parent")]
      ]
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
  await callback.answer()


@dp.callback_query(F.data == "parent_info_help")
async def show_info_help(callback: types.CallbackQuery):
  data = load_data()
  cls_data = data.get("1B", {})
  text = cls_data.get("info_help", "-")
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="🔙 Назад", callback_data="role_parent")]
      ]
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
  await callback.answer()


@dp.callback_query(F.data == "send_medical_note")
async def send_medical_note_start(
    callback: types.CallbackQuery, state: FSMContext
):
  await callback.message.answer(
      "📄 Напишите ФИО ребенка и причину (или отправьте фото справки):"
  )
  await state.set_state(ParentSendNote.waiting_for_note)
  await callback.answer()


@dp.message(ParentSendNote.waiting_for_note)
async def process_parent_note(message: types.Message, state: FSMContext):
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔙 В кабинет родителя", callback_data="role_parent"
              )
          ]
      ]
  )
  await message.answer(
      "✅ **Заявление/справка успешно передана учителю!**",
      reply_markup=kb,
      parse_mode="Markdown",
  )


# --- Редактирование FSM учителем ---
@dp.callback_query(F.data == "teacher_call_parent_start")
async def teacher_call_parent_start(
    callback: types.CallbackQuery, state: FSMContext
):
  await callback.message.answer("🚨 Введите ФИО ученика и причину вызова:")
  await state.set_state(TeacherEdit.waiting_for_call_parent)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_call_parent)
async def process_call_parent(message: types.Message, state: FSMContext):
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔙 В панель учителя", callback_data="role_teacher"
              )
          ]
      ]
  )
  await message.answer(
      f"🚨 **Срочное уведомление отправлено родителю!**\nПричина: {message.text}",
      reply_markup=kb,
      parse_mode="Markdown",
  )


@dp.callback_query(F.data == "edit_important_notes")
async def edit_important_notes_start(
    callback: types.CallbackQuery, state: FSMContext
):
  await callback.message.answer(
      "⚠️ Введите информацию об аллергиях и особенностях здоровья детей:"
  )
  await state.set_state(TeacherEdit.waiting_for_important_notes)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_important_notes)
async def process_important_notes(message: types.Message, state: FSMContext):
  data = load_data()
  data["1B"]["important_notes"] = (
      f"⚠️ **ВАЖНО О ДЕТЯХ (Аллергии и медицинские отметки):**\n{message.text}"
  )
  save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔙 В панель учителя", callback_data="role_teacher"
              )
          ]
      ]
  )
  await message.answer(
      "✅ **Информация об аллергиях обновлена!**",
      reply_markup=kb,
      parse_mode="Markdown",
  )


@dp.callback_query(F.data == "edit_poll")
async def edit_poll_start(callback: types.CallbackQuery, state: FSMContext):
  await callback.message.answer("📊 Введите тему нового опроса класса:")
  await state.set_state(TeacherEdit.waiting_for_poll)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_poll)
async def process_poll(message: types.Message, state: FSMContext):
  data = load_data()
  data["1B"]["active_poll"] = (
      f"📊 **Активный опрос класса:**\nТема: {message.text}\n• Вариант 1: Да\n•"
      " Вариант 2: Нет"
  )
  save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔙 В панель учителя", callback_data="role_teacher"
              )
          ]
      ]
  )
  await message.answer(
      "✅ **Опрос успешно открыт для класса!**",
      reply_markup=kb,
      parse_mode="Markdown",
  )


@dp.callback_query(F.data == "edit_treasury")
async def edit_treasury_start(
    callback: types.CallbackQuery, state: FSMContext
):
  await callback.message.answer("💰 Введите данные по кассе и фонду класса:")
  await state.set_state(TeacherEdit.waiting_for_treasury)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_treasury)
async def process_treasury(message: types.Message, state: FSMContext):
  data = load_data()
  data["1B"]["treasury_report"] = (
      f"💰 **Фонд класса (Отчёт казначея):**\n{message.text}"
  )
  save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔙 В панель учителя", callback_data="role_teacher"
              )
          ]
      ]
  )
  await message.answer(
      "✅ **Отчёт кассы обновлен!**", reply_markup=kb, parse_mode="Markdown"
  )


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


@dp.message(TeacherEdit.waiting_for_chairman_phone)
async def process_chairman_phone(message: types.Message, state: FSMContext):
  await state.update_data(chairman_phone=message.text)
  await message.answer("📝 Введите **ФИО казначея** родительского комитета:")
  await state.set_state(TeacherEdit.waiting_for_treasurer_name)


@dp.message(TeacherEdit.waiting_for_treasurer_name)
async def process_treasurer_name(message: types.Message, state: FSMContext):
  await state.update_data(treasurer_name=message.text)
  await message.answer("📞 Введите **телефон казначея**:")
  await state.set_state(TeacherEdit.waiting_for_treasurer_phone)


@dp.message(TeacherEdit.waiting_for_treasurer_phone)
async def process_treasurer_phone(message: types.Message, state: FSMContext):
  data = load_data()
  user_data = await state.get_data()
  data["1B"].update({
      "chairman_name": user_data["chairman_name"],
      "chairman_phone": user_data["chairman_phone"],
      "treasurer_name": user_data["treasurer_name"],
      "treasurer_phone": message.text,
  })
  save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔙 В панель учителя", callback_data="role_teacher"
              )
          ]
      ]
  )
  await message.answer(
      "✅ **Контакты родкомитета обновлены!**",
      reply_markup=kb,
      parse_mode="Markdown",
  )


@dp.callback_query(F.data == "edit_meeting")
async def edit_meeting_start(callback: types.CallbackQuery, state: FSMContext):
  await callback.message.answer(
      "📅 Введите информацию о новом родительском собрании:"
  )
  await state.set_state(TeacherEdit.waiting_for_meeting)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_meeting)
async def process_new_meeting(message: types.Message, state: FSMContext):
  data = load_data()
  data["1B"]["next_meeting"] = message.text
  save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔙 В панель учителя", callback_data="role_teacher"
              )
          ]
      ]
  )
  await message.answer(
      "✅ **Собрание обновлено!**", reply_markup=kb, parse_mode="Markdown"
  )


@dp.callback_query(F.data == "edit_announcement")
async def edit_announcement_start(
    callback: types.CallbackQuery, state: FSMContext
):
  await callback.message.answer("📢 Введите текст нового объявления:")
  await state.set_state(TeacherEdit.waiting_for_announcement)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_announcement)
async def process_new_announcement(message: types.Message, state: FSMContext):
  data = load_data()
  data["1B"]["announcement"] = message.text
  save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔙 В панель учителя", callback_data="role_teacher"
              )
          ]
      ]
  )
  await message.answer(
      "✅ **Объявление опубликовано!**", reply_markup=kb, parse_mode="Markdown"
  )


@dp.callback_query(F.data == "edit_holidays")
async def edit_holidays_start(callback: types.CallbackQuery, state: FSMContext):
  await callback.message.answer("🎉 Введите праздники и мероприятия:")
  await state.set_state(TeacherEdit.waiting_for_holidays)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_holidays)
async def process_new_holidays(message: types.Message, state: FSMContext):
  data = load_data()
  data["1B"]["holidays"] = message.text
  save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔙 В панель учителя", callback_data="role_teacher"
              )
          ]
      ]
  )
  await message.answer(
      "✅ **Праздники обновлены!**", reply_markup=kb, parse_mode="Markdown"
  )


@dp.callback_query(F.data == "edit_homework")
async def edit_homework_start(callback: types.CallbackQuery, state: FSMContext):
  await callback.message.answer("📚 Введите домашнее задание:")
  await state.set_state(TeacherEdit.waiting_for_homework)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_homework)
async def process_new_homework(message: types.Message, state: FSMContext):
  data = load_data()
  data["1B"]["homework"] = message.text
  save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔙 В панель учителя", callback_data="role_teacher"
              )
          ]
      ]
  )
  await message.answer(
      "✅ **Домашнее задание обновлено!**",
      reply_markup=kb,
      parse_mode="Markdown",
  )


@dp.callback_query(F.data == "edit_schedule")
async def edit_schedule_start(callback: types.CallbackQuery, state: FSMContext):
  await callback.message.answer("⏰ Введите расписание уроков:")
  await state.set_state(TeacherEdit.waiting_for_schedule)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_schedule)
async def process_new_schedule(message: types.Message, state: FSMContext):
  data = load_data()
  data["1B"]["schedule"] = message.text
  save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔙 В панель учителя", callback_data="role_teacher"
              )
          ]
      ]
  )
  await message.answer(
      "✅ **Расписание обновлено!**", reply_markup=kb, parse_mode="Markdown"
  )


@dp.callback_query(F.data == "edit_info_help")
async def edit_info_help_start(
    callback: types.CallbackQuery, state: FSMContext
):
  await callback.message.answer("ℹ️ Введите текст справки и правил школы:")
  await state.set_state(TeacherEdit.waiting_for_info_help)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_info_help)
async def process_new_info_help(message: types.Message, state: FSMContext):
  data = load_data()
  data["1B"]["info_help"] = message.text
  save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔙 В панель учителя", callback_data="role_teacher"
              )
          ]
      ]
  )
  await message.answer(
      "✅ **Справка и правила школы обновлены!**",
      reply_markup=kb,
      parse_mode="Markdown",
  )


@dp.callback_query(F.data == "edit_students_list")
async def edit_students_list_start(
    callback: types.CallbackQuery, state: FSMContext
):
  await callback.message.answer("📋 Введите новый список учеников класса:")
  await state.set_state(TeacherEdit.waiting_for_students_list)
  await callback.answer()


@dp.message(TeacherEdit.waiting_for_students_list)
async def process_new_students_list(message: types.Message, state: FSMContext):
  data = load_data()
  data["1B"]["students_list"] = f"📋 **Список класса (1 «В»):**\n{message.text}"
  save_data(data)
  await state.clear()
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔙 В панель учителя", callback_data="role_teacher"
              )
          ]
      ]
  )
  await message.answer(
      "✅ **Список класса обновлен!**", reply_markup=kb, parse_mode="Markdown"
  )


@dp.callback_query(F.data == "teacher_students_view")
async def teacher_students_view(callback: types.CallbackQuery):
  data = load_data()
  cls_data = data.get("1B", {})
  students = cls_data.get("students_list", "Список класса пока не заполнен.")
  attendance = cls_data.get("attendance_log", "Журнал пуст.")
  text = f"{students}\n\n{attendance}"
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="✏️ Обновить список класса",
                  callback_data="edit_students_list",
              )
          ],
          [
              InlineKeyboardButton(
                  text="🔙 В панель учителя", callback_data="role_teacher"
              )
          ],
      ]
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
  await callback.answer()


@dp.callback_query(F.data == "teacher_sub_status")
async def show_sub_status(callback: types.CallbackQuery):
  data = load_data()
  sub = data.get("1B", {}).get("subscription", {})
  text = (
      f"💳 **Статус подписки платформы:**\n\n"
      f"• **Текущий тариф:** {sub.get('status', 'Пробный период')}\n"
      f"• **Осталось дней:** {sub.get('days_left', 30)} дн.\n"
      f"• **Стоимость продления:** {sub.get('price', '500 сом / мес')}\n\n"
      f"🔔 *Уведомление за 3 дня до окончания будет отправлено автоматически.*"
  )
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔙 В панель учителя", callback_data="role_teacher"
              )
          ]
      ]
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
  await callback.answer()


# --- Обработка кликов посещаемости ---
@dp.callback_query(F.data.in_(["action_pickup", "action_late", "action_skip"]))
async def parent_actions(callback: types.CallbackQuery):
  actions = {
      "action_pickup": (
          "✅ Запрос отправлен! Учитель уведомлен, что вы забираете ребёнка."
      ),
      "action_late": "⚠️ Учитель получил уведомление об опоздании.",
      "action_skip": (
          "🔴 Отметка сохранена: ребёнок сегодня не пришёл в школу."
      ),
  }
  await callback.answer(actions.get(callback.data, "Готово!"), show_alert=True)


# --- Веб-сервер 24/7 ---
async def handle(request):
  return web.Response(text="Bot is running 24/7!")


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
