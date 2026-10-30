import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Инициализация логов
logging.basicConfig(level=logging.INFO)

# Получаем токен бота из переменных окружения Render
TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- СТАРТОВОЕ МЕНЮ С УЧЕТОМ РОЛЕЙ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    
    # Кнопки выбора ролей и интерфейсов с душевным подходом
    builder.button(text="👑 Директор (Ритм школы и сводка)", callback_data="role_director")
    builder.button(text="📚 Завуч (Расписание и замеры)", callback_data="role_deputy")
    builder.button(text="👩‍🏫 Учитель (Журнал и экстренная кнопка)", callback_data="role_teacher")
    builder.button(text="👨‍👩‍👧 Родитель (Забота и логистика)", callback_data="role_parent")
    builder.button(text="🎒 Ученик (Мотивация и расписание)", callback_data="role_student")
    builder.button(text="🛠️ Работники школы (Столовая, дворники)", callback_data="role_service")
    
    builder.adjust(1) # Выстраиваем кнопки в один столбец для удобства
    
    welcome_text = (
        "Бисмилляхи рахмани рахим!\n\n"
        "Добро пожаловать в цифровую экосистему школы, где на первом месте стоит человек, "
        "психологический комфорт, безопасность и забота.\n\n"
        "Пожалуйста, выберите вашу роль для входа в систему:"
    )
    
    await message.answer(welcome_text, reply_markup=builder.as_markup())


# --- ОБРАБОТЧИК РОЛИ УЧИТЕЛЯ И ЭКСТРЕННЫХ КНОПОК ---
@dp.callback_query(lambda c: c.data == "role_teacher")
async def teacher_panel(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Электронный журнал за 10 сек", callback_data="t_journal")
    builder.button(text="🚨 Экстренный вызов (Красная кнопка)", callback_data="t_emergency")
    builder.button(text="🔙 На главную", callback_data="back_home")
    builder.adjust(1)
    
    text = (
        "👩‍🏫 **Панель классного руководителя / учителя**\n\n"
        "• Отметки заносятся с заботой (например: «Медицинский отгул / Восстановление»).\n"
        "• Возле каждого ученика доступна мигающая красная кнопка экстренной связи с родителем.\n"
        "• Маркеры здоровья (аллергии и особенности) всегда под рукой."
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


# --- ОБРАБОТЧИК РОЛИ РОДИТЕЛЯ И КОМПЛИМЕНТОВ ---
@dp.callback_query(lambda c: c.data == "role_parent")
async def parent_panel(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="🎒 Отметка: Ребенок забран из школы", callback_data="p_pickup")
    builder.button(text="🗳️ Опросник родкомитета (Едем на каникулы?)", callback_data="p_poll")
    builder.button(text="💰 Нужды класса (Сборы и отчет)", callback_data="p_needs")
    builder.button(text="🔙 На главную", callback_data="back_home")
    builder.adjust(1)
    
    text = (
        "👨‍👩‍👧 **Панель заботливого родителя**\n\n"
        "Здесь вы можете видеть логистику, участвовать в жизни класса без лишних споров и "
        "получать теплые слова поддержки за ваш родительский труд!"
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


# --- ЭМУЛЯЦИЯ ЗАБОТЛИВОГО УВЕДОМЛЕНИЯ ПРИ ЗАБОРЕ РЕБЕНКА ---
@dp.callback_query(lambda c: c.data == "p_pickup")
async def parent_pickup_alert(callback: types.CallbackQuery):
    compliment_text = (
        "❤️ **Уведомление системы:**\n\n"
        "Вы потрясающий родитель! Спасибо за вашу заботу и любовь.\n"
        "Ваш ребенок — настоящий гений и уникальная личность. Пусть этот день принесет вам радость!"
    )
    await callback.message.answer(compliment_text)
    await callback.answer("Ребенок успешно отмечен!")


# --- ВОЗВРАТ НА ГЛАВНУЮ ---
@dp.callback_query(lambda c: c.data == "back_home")
async def back_to_home(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="👑 Директор", callback_data="role_director")
    builder.button(text="📚 Завуч", callback_data="role_deputy")
    builder.button(text="👩‍🏫 Учитель", callback_data="role_teacher")
    builder.button(text="👨‍👩‍👧 Родитель", callback_data="role_parent")
    builder.button(text="🎒 Ученик", callback_data="role_student")
    builder.button(text="🛠️ Работники школы", callback_data="role_service")
    builder.adjust(1)
    
    await callback.message.edit_text("Главное меню. Выберите вашу роль:", reply_markup=builder.as_markup())
    await callback.answer()


# Главная точка входа для запуска бота
if __name__ == "__main__":
    import asyncio
    async def main():
        await dp.start_polling(bot)
    asyncio.run(main())
