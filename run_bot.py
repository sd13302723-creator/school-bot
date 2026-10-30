import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
# Импортируем вашу основную логику из school_bot.py
from school_bot import dp, bot

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
