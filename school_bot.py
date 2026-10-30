import json
import os
import asyncio
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
            "treasurer_phone": "+996 700 987-654"
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

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧑‍🏫 Классный руководитель", callback_data="role_teacher")],
        [InlineKeyboardButton(text="👪 Родителю", callback_data="role_parent")]
    ])
    await message.answer(
        "🏛 **Система безопасности «Школа» (1 «В»)**\n\n"
        "⭐ Единая платформа контроля посещаемости и связи\n\n"
        "Пожалуйста, выберите вашу роль для входа:",
        reply_markup=kb, parse_mode="Markdown"
    )

@dp.callback_query(F.data == "role_teacher")
async def teacher_menu(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Изменить контакты родкомитета", callback_data="edit_rodkom")],
        [InlineKeyboardButton(text="🔙 На главную", callback_data="back_to_main")]
    ])
    await callback.message.edit_text(
        "🧑‍🏫 **Панель классного руководителя**\n\nВыберите нужное действие:",
        reply_markup=kb, parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "role_parent")
async def parent_menu(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Забрать ребенка", callback_data="action_pickup")],
        [InlineKeyboardButton(text="🟡 Опоздаем на урок", callback_data="action_late")],
        [InlineKeyboardButton(text="🔴 Пропустим / Причина...", callback_data="action_skip")],
        [InlineKeyboardButton(text="👥 Родительский комитет (контакты)", callback_data="rodkom_menu")],
        [InlineKeyboardButton(text="🔙 На главную", callback_data="back_to_main")]
    ])
    await callback.message.edit_text(
        "👪 **Кабинет родителя (1 «В» класс)**\n\nВыберите нужное действие:",
        reply_markup=kb, parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧑‍🏫 Классный руководитель", callback_data="role_teacher")],
        [InlineKeyboardButton(text="👪 Родителю", callback_data="role_parent")]
    ])
    await callback.message.edit_text(
        "🏛 **Система безопасности «Школа» (1 «В»)**\n\n"
        "Пожалуйста, выберите вашу роль для входа:",
        reply_markup=kb, parse_mode="Markdown"
    )
    await callback.answer()

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
        f"Нажмите на номер телефона, чтобы скопировать его."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="role_parent")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "edit_rodkom")
async def edit_rodkom_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("📝 Введите **ФИО председателя** родительского комитета:")
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
    data["1B"] = {
        "chairman_name": user_data["chairman_name"],
        "chairman_phone": user_data["chairman_phone"],
        "treasurer_name": user_data["treasurer_name"],
        "treasurer_phone": message.text
    }
    save_data(data)
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 В панель учителя", callback_data="role_teacher")]
    ])
    await message.answer("✅ **Контакты родительского комитета успешно обновлены!**", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.in_(["action_pickup", "action_late", "action_skip"]))
async def parent_actions(callback: types.CallbackQuery):
    actions = {
        "action_pickup": "✅ Запрос отправлен! Учитель уведомлен, что вы забираете ребёнка.",
        "action_late": "⚠️ Учитель получил уведомление об опоздании.",
        "action_skip": "📝 Причина пропуска записана."
    }
    await callback.answer(actions.get(callback.data, "Готово!"), show_alert=True)

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
