import os
import threading
import logging
import asyncio
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from aiogram import Bot, Dispatcher, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Получение токена и порта из системного окружения (для Render)
TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

# --- 1. ВЕБ-СЕРВЕР ДЛЯ RENDER (Фоновый поток) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"School Bot is alive!")
    def log_message(self, format, *args):
        pass

def run_web_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthCheckHandler)
    server.serve_forever()

# --- 2. ИНИЦИАЛИЗАЦИЯ БОТА И СОСТОЯНИЙ ---
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class ParentState(StatesGroup):
    waiting_for_absence_reason = State()
    waiting_for_parent_chat_message = State()

# База данных класса на 38 учеников с реальными именами
class_data = {
    "1_v": {
        "class_name": "1 «В»",
        "teacher_id": None,     # ID учителя
        "parents_ids": set(),   # ID всех родителей для рассылок
        # История сообщений родительского чата
        "parent_chat_messages": [],
        # Список родительского комитета (ФИО + телефон)
        "parent_committee": [
            {"name": "Алина (Председатель)", "phone": "+996 555 123-456"},
            {"name": "Марат (Казначей)", "phone": "+996 700 987-654"}
        ],
        "events": [
            {"title": "🎄 Новогодняя ёлка", "date": "25 декабря в 10:00"},
            {"title": "🌷 Праздник 8 Марта", "date": "7 марта в 11:00"}
        ],
        "meeting_poll": {"yes": 0, "no": 0},
        # Полный список 38 учеников
        "students": [
            {"id": "s1", "name": "Абдурасулов Алихан", "status": "В школе", "certificate": "Нет"},
            {"id": "s2", "name": "Айткулова Айма", "status": "В школе", "certificate": "Нет"},
            {"id": "s3", "name": "Амитова Аруузат", "status": "В школе", "certificate": "Нет"},
            {"id": "s4", "name": "Бектуров Атай", "status": "В школе", "certificate": "Нет"},
            {"id": "s5", "name": "Жаныбекова Айлин", "status": "В школе", "certificate": "Нет"},
            {"id": "s6", "name": "Касымов Эрбол", "status": "В школе", "certificate": "Нет"},
            {"id": "s7", "name": "Тургунбек уулу Самир", "status": "В школе", "certificate": "Нет"},
            {"id": "s8", "name": "Мурзабекова Сафия", "status": "В школе", "certificate": "Нет"},
            {"id": "s9", "name": "Осмонов Тимур", "status": "В школе", "certificate": "Нет"},
            {"id": "s10", "name": "Шаршеева Эмина", "status": "В школе", "certificate": "Нет"},
            {"id": "s11", "name": "Алиев Данияр", "status": "В школе", "certificate": "Нет"},
            {"id": "s12", "name": "Бакиров Амир", "status": "В школе", "certificate": "Нет"},
            {"id": "s13", "name": "Ибрагимова Аяна", "status": "В школе", "certificate": "Нет"},
            {"id": "s14", "name": "Исмаилов Нурэпи", "status": "В школе", "certificate": "Нет"},
            {"id": "s15", "name": "Нурланова Аделина", "status": "В школе", "certificate": "Нет"},
            {"id": "s16", "name": "Акунов Арсен", "status": "В школе", "certificate": "Нет"},
            {"id": "s17", "name": "Алыкулов Эмир", "status": "В школе", "certificate": "Нет"},
            {"id": "s18", "name": "Асанбекова Амина", "status": "В школе", "certificate": "Нет"},
            {"id": "s19", "name": "Бактыбеков Адилет", "status": "В школе", "certificate": "Нет"},
            {"id": "s20", "name": "Болотбекова Айзере", "status": "В школе", "certificate": "Нет"},
            {"id": "s21", "name": "Данияров Раян", "status": "В школе", "certificate": "Нет"},
            {"id": "s22", "name": "Жолдошев Бакай", "status": "В школе", "certificate": "Нет"},
            {"id": "s23", "name": "Исаков Имран", "status": "В школе", "certificate": "Нет"},
            {"id": "s24", "name": "Калыбекова Раяна", "status": "В школе", "certificate": "Нет"},
            {"id": "s25", "name": "Кубанычбекова Салима", "status": "В школе", "certificate": "Нет"},
            {"id": "s26", "name": "Мамытов Умар", "status": "В школе", "certificate": "Нет"},
            {"id": "s27", "name": "Медеров Аян", "status": "В школе", "certificate": "Нет"},
            {"id": "s28", "name": "Назаров Артур", "status": "В школе", "certificate": "Нет"},
            {"id": "s29", "name": "Омурзакова Аэлита", "status": "В школе", "certificate": "Нет"},
            {"id": "s30", "name": "Рыскулов Дастан", "status": "В школе", "certificate": "Нет"},
            {"id": "s31", "name": "Садырова Ясмина", "status": "В школе", "certificate": "Нет"},
            {"id": "s32", "name": "Султанова Аделия", "status": "В школе", "certificate": "Нет"},
            {"id": "s33", "name": "Таалайбеков Элдар", "status": "В школе", "certificate": "Нет"},
            {"id": "s34", "name": "Темиров Али", "status": "В школе", "certificate": "Нет"},
            {"id": "s35", "name": "Токтогулов Даниял", "status": "В школе", "certificate": "Нет"},
            {"id": "s36", "name": "Уланов Эмирхан", "status": "В школе", "certificate": "Нет"},
            {"id": "s37", "name": "Эркинбекова Арууке", "status": "В школе", "certificate": "Нет"},
            {"id": "s38", "name": "Юсупова Альфия", "status": "В школе", "certificate": "Нет"}
        ]
    }
}

# --- 3. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
async def broadcast_to_parents(text: str, exclude_id=None):
    parents = class_data["1_v"]["parents_ids"]
    for p_id in parents:
        if p_id == exclude_id:
            continue
        try:
            await bot.send_message(p_id, text, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Не удалось отправить сообщение родителям: {e}")

# --- 4. ОБРАБОТЧИКИ КОМАНД И КНОПОК ---

@dp.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👩‍🏫 Классный руководитель", callback_data="role_teacher")],
        [InlineKeyboardButton(text="👨‍👩‍👧 Родитель", callback_data="role_parent")]
    ])
    await message.answer(
        "🏛 **Система безопасности «Школа» (1 «В»)**\n\n"
        "⭐ *Единая платформа контроля посещаемости и связи*\n\n"
        "Пожалуйста, выберите вашу роль для входа:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# --- КАБИНЕТ УЧИТЕЛЯ ---

@dp.callback_query(F.data == "role_teacher")
async def process_teacher(callback: CallbackQuery):
    class_data["1_v"]["teacher_id"] = callback.from_user.id
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Журнал класса (все 38 учеников)", callback_data="teacher_list")],
        [InlineKeyboardButton(text="📄 Управление справками", callback_data="teacher_certificates_menu")],
        [InlineKeyboardButton(text="📊 Опрос по собранию", callback_data="teacher_poll_stats")],
        [InlineKeyboardButton(text="👥 Родительский комитет", callback_data="teacher_committee")],
        [InlineKeyboardButton(text="🎉 Праздники и мероприятия", callback_data="teacher_events")],
        [InlineKeyboardButton(text="🔔 Напомнить о ДЗ / Безопасности", callback_data="teacher_reminders")]
    ])
    
    await callback.message.edit_text(
        "👩‍🏫 **Кабинет классного руководителя (1 «В»)**\n\n"
        "Выберите нужный раздел управления:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "teacher_list")
async def show_teacher_list(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить список", callback_data="teacher_list")],
        [InlineKeyboardButton(text="⬅ Назад в меню", callback_data="role_teacher")]
    ])
    
    in_school = sum(1 for s in class_data["1_v"]["students"] if s["status"] == "В школе")
    late = sum(1 for s in class_data["1_v"]["students"] if "Опоздает" in s["status"])
    home = sum(1 for s in class_data["1_v"]["students"] if "Забран" in s["status"])
    
    text = (
        f"📋 **Журнал класса 1 «В» (всего 38 учеников):**\n"
        f"🏫 В школе: **{in_school}** | 🟡 Опоздают: **{late}** | ✅ Дома: **{home}**\n\n"
    )
    for idx, student in enumerate(class_data["1_v"]["students"], start=1):
        st = student["status"]
        cert = f" | 📄 Справка: {student['certificate']}" if student['certificate'] != "Нет" else ""
        icon = "🏫 В школе" if st == "В школе" else ("🟡 Опоздает" if "Опоздает" in st else f"🔴 {st}")
        text += f"{idx}. {student['name']} — {icon}{cert}\n"
        
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "teacher_certificates_menu")
async def teacher_certificates_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отметить: Справка сдана", callback_data="cert_mark_given")],
        [InlineKeyboardButton(text="⬅ Назад в меню", callback_data="role_teacher")]
    ])
    text = "📄 **Раздел справок:**\n\nЗдесь отображаются ученики, у которых отмечено наличие справки (бумажную версию родитель передает лично в руки).\n\n"
    
    found = False
    for idx, student in enumerate(class_data["1_v"]["students"], start=1):
        if student["certificate"] != "Нет":
            text += f"{idx}. {student['name']} — 📄 Справка: {student['certificate']}\n"
            found = True
            
    if not found:
        text += "_Пока нет отмеченных справок._"

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "cert_mark_given")
async def cert_mark_given(callback: CallbackQuery):
    class_data["1_v"]["students"][6]["certificate"] = "Сдана (вручено учителю)"  # Пример для Самира (№7)
    await callback.answer("Статус справки обновлен! ✅", show_alert=True)
    await teacher_certificates_menu(callback)

@dp.callback_query(F.data == "teacher_poll_stats")
async def teacher_poll_stats(callback: CallbackQuery):
    poll = class_data["1_v"]["meeting_poll"]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Запустить опрос в чат", callback_data="send_poll_to_parents")],
        [InlineKeyboardButton(text="⬅ Назад в меню", callback_data="role_teacher")]
    ])
    text = f"📊 **Результаты опроса по собранию:**\n\n✅ Будут: **{poll['yes']}**\n❌ Не смогут: **{poll['no']}**"
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "send_poll_to_parents")
async def send_poll_to_parents(callback: CallbackQuery):
    class_data["1_v"]["meeting_poll"] = {"yes": 0, "no": 0}
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Буду на собрании", callback_data="poll_vote_yes")],
        [InlineKeyboardButton(text="❌ Не смогу присутствовать", callback_data="poll_vote_no")]
    ])
    for p_id in class_data["1_v"]["parents_ids"]:
        try:
            await bot.send_message(p_id, "📊 **Опрос по собранию:** Будете ли вы присутствовать?", reply_markup=keyboard, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Ошибка: {e}")
    await callback.answer("Опрос отправлен родителям! ✅", show_alert=True)

@dp.callback_query(F.data == "teacher_committee")
async def teacher_committee(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅ Назад в меню", callback_data="role_teacher")]])
    text = "👥 **Родительский комитет:**\n\n" + "\n".join([f"• {m['name']} — 📞 {m['phone']}" for m in class_data["1_v"]["parent_committee"]])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "teacher_events")
async def teacher_events(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Разослать праздники", callback_data="broadcast_events")],
        [InlineKeyboardButton(text="⬅ Назад в меню", callback_data="role_teacher")]
    ])
    text = "🎉 **Праздники и мероприятия:**\n\n" + "\n".join([f"• {ev['title']} — {ev['date']}" for ev in class_data["1_v"]["events"]])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "broadcast_events")
async def broadcast_events(callback: CallbackQuery):
    text = "🎉 **График мероприятий класса:**\n\n" + "\n".join([f"• {ev['title']} — {ev['date']}" for ev in class_data["1_v"]["events"]])
    await broadcast_to_parents(text)
    await callback.answer("График отправлен! ✅", show_alert=True)

@dp.callback_query(F.data == "teacher_reminders")
async def teacher_reminders(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Напомнить о ДЗ", callback_data="send_homework")],
        [InlineKeyboardButton(text="🛡 Напомнить о безопасности", callback_data="send_safety")],
        [InlineKeyboardButton(text="⬅ Назад в меню", callback_data="role_teacher")]
    ])
    await callback.message.edit_text("🔔 **Выберите напоминание для рассылки:**", reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "send_homework")
async def send_homework_msg(callback: CallbackQuery):
    await broadcast_to_parents("📚 **Напоминание о домашнем задании:** проверьте выполнение уроков на завтра.")
    await callback.answer("Отправлено! ✅", show_alert=True)

@dp.callback_query(F.data == "send_safety")
async def send_safety_msg(callback: CallbackQuery):
    await broadcast_to_parents("🛡 **Напоминание о безопасности:** повторите с детьми правила поведения по дороге в школу.")
    await callback.answer("Отправлено! ✅", show_alert=True)

# --- КАБИНЕТ РОДИТЕЛЯ ---

@dp.callback_query(F.data == "role_parent")
async def process_parent(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    class_data["1_v"]["parents_ids"].add(callback.from_user.id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Забрать: Тургунбек уулу Самир", callback_data="status_pickup_s7")],
        [InlineKeyboardButton(text="🟡 Опоздаем на урок", callback_data="status_late_s7")],
        [InlineKeyboardButton(text="🔴 Пропустим / Причина...", callback_data="ask_custom_reason")],
        [InlineKeyboardButton(text="💬 Общий чат родителей", callback_data="parent_chat_main")],
        [InlineKeyboardButton(text="👥 Родительский комитет (телефоны)", callback_data="parent_view_committee")],
        [InlineKeyboardButton(text="🎉 Праздники", callback_data="parent_view_events")],
        [InlineKeyboardButton(text="🚨 Экстренная связь с учителем", callback_data="emergency_contact")]
    ])
    await callback.message.edit_text(
        "👨‍👩‍👧 **Кабинет родителя (1 «В»)**\n\nВыберите нужное действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "ask_custom_reason")
async def ask_custom_reason(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ParentState.waiting_for_absence_reason)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅ Отмена", callback_data="role_parent")]])
    await callback.message.edit_text(
        "✍️ **Напишите причину пропуска занятий ответным сообщением:**\n\n"
        "(Если ребёнок пропускает 3 и более дней, бумажную справку нужно принести лично учителю)",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(ParentState.waiting_for_absence_reason)
async def process_custom_reason_text(message: Message, state: FSMContext):
    reason_text = message.text
    target_student = class_data["1_v"]["students"][6]  # Самир (№7)
    target_student["status"] = f"Отсутствует ({reason_text})"
    target_student["certificate"] = "Требуется (пропуск)"
    
    await message.answer(f"✅ **Причина передана учителю:**\n_{reason_text}_ 🌸", parse_mode="Markdown")
    
    teacher_id = class_data["1_v"]["teacher_id"]
    if teacher_id:
        try:
            await bot.send_message(teacher_id, f"🔴 **{target_student['name']}** отсутствует.\n📝 Причина: *{reason_text}*", parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Ошибка: {e}")
    await state.clear()

@dp.callback_query(F.data.startswith("status_"))
async def process_status_change(callback: CallbackQuery):
    data = callback.data
    target_student = class_data["1_v"]["students"][6]  # Самир (№7)
    teacher_id = class_data["1_v"]["teacher_id"]
    
    if "pickup" in data:
        target_student["status"] = "Забран (Дома)"
        resp = "💚 **Всё отлично! Ребёнок дома и в безопасности. 🌸**"
        t_msg = f"🔔 **1 «В»**: {target_student['name']} — забрали домой (отметка родителя)."
    elif "late" in data:
        target_student["status"] = "Опоздает"
        resp = "🟡 Учитель предупреждён об опоздании."
        t_msg = f"🟡 **1 «В»**: {target_student['name']} сегодня опоздает."

    await callback.message.edit_text(resp, parse_mode="Markdown")
    if teacher_id:
        try:
            await bot.send_message(teacher_id, t_msg, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Ошибка: {e}")
    await callback.answer()

# --- СВОБОДНЫЙ ЧАТ РОДИТЕЛЕЙ ---

@dp.callback_query(F.data == "parent_chat_main")
async def parent_chat_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Написать в общий чат родителей", callback_data="write_to_parent_chat")],
        [InlineKeyboardButton(text="🔄 Обновить ленту чата", callback_data="parent_chat_main")],
        [InlineKeyboardButton(text="⬅ Назад в меню", callback_data="role_parent")]
    ])
    
    chat_history = class_data["1_v"]["parent_chat_messages"]
    text = "💬 **Свободный чат родителей 1 «В» класса**\n_(Здесь можно обсудить организационные вопросы, сборы и обмениваться мнениями)_\n\n"
    
    if not chat_history:
        text += "_В чате пока нет сообщений. Напишите первое сообщение!_"
    else:
        for msg_info in chat_history[-10:]:
            text += f"• **{msg_info['sender']}**: {msg_info['text']} _({msg_info['time']})_\n"
            
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "write_to_parent_chat")
async def write_to_parent_chat(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ParentState.waiting_for_parent_chat_message)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Отмена", callback_data="parent_chat_main")]
    ])
    await callback.message.edit_text(
        "✍️ **Напишите ваше сообщение в общий чат родителей:**",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(ParentState.waiting_for_parent_chat_message)
async def process_parent_chat_message(message: Message, state: FSMContext):
    user_text = message.text
    user_name = message.from_user.full_name or "Родитель"
    current_time = datetime.now().strftime("%H:%M")
    
    class_data["1_v"]["parent_chat_messages"].append({
        "sender": user_name,
        "text": user_text,
        "time": current_time
    })
    
    notification_text = f"💬 **Сообщение в чат родителей от {user_name}** ({current_time}):\n\n{user_text}"
    await broadcast_to_parents(notification_text, exclude_id=message.from_user.id)
    
    await message.answer(
        "✅ **Ваше сообщение успешно отправлено в общий чат родителей!**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Вернуться в чат", callback_data="parent_chat_main")]
        ]),
        parse_mode="Markdown"
    )
    await state.clear()

@dp.callback_query(F.data.startswith("poll_vote_"))
async def process_poll_vote(callback: CallbackQuery):
    if "yes" in callback.data:
        class_data["1_v"]["meeting_poll"]["yes"] += 1
        await callback.message.edit_text("✅ Спасибо! Вы будете на собрании.", parse_mode="Markdown")
    else:
        class_data["1_v"]["meeting_poll"]["no"] += 1
        await callback.message.edit_text("❌ Спасибо! Вы не сможете прийти.", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "parent_view_events")
async def parent_view_events(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅ Назад", callback_data="role_parent")]])
    text = "🎉 **Праздники:**\n\n" + "\n".join([f"• {ev['title']} — {ev['date']}" for ev in class_data["1_v"]["events"]])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "parent_view_committee")
async def parent_view_committee(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅ Назад", callback_data="role_parent")]])
    text = "👥 **Родительский комитет (контакты для связи):**\n\n"
    for m in class_data["1_v"]["parent_committee"]:
        text += f"• **{m['name']}**\n  📞 Телефон: `{m['phone']}`\n\n"
    text += "_Нажмите на номер телефона, чтобы скопировать его и позвонить._"
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "emergency_contact")
async def emergency_contact_info(callback: CallbackQuery):
    teacher_id = class_data["1_v"]["teacher_id"]
    if teacher_id:
        try:
            await bot.send_message(teacher_id, "🚨 **ВНИМАНИЕ! Экстренное сообщение от родителя!**")
        except Exception as e:
            logging.error(f"Ошибка: {e}")
    await callback.message.edit_text("🚨 Экстренное сообщение отправлено учителю!", parse_mode="Markdown")
    await callback.answer()

# --- 5. ЕДИНАЯ ТОЧКА ЗАПУСКА ---
async def main():
    threading.Thread(target=run_web_server, daemon=True).start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
