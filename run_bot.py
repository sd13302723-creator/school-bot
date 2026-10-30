import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="⚙️ Изменить контакты родкомитета")],
            [types.KeyboardButton(text="📅 Назначить собрание")],
            [types.KeyboardButton(text="📢 Написать объявлению классу")],
            [types.KeyboardButton(text="🔙 На главную")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "👋 Панель классного руководителя.\n\nВыберите нужное управление:",
        reply_markup=builder
    )

async def handle(request):
    return web.Response(text="School SaaS Bot is running 24/7!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    logging.basicConfig(level=logging.INFO)
    await asyncio.gather(
        web_server(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
