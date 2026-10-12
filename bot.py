"""РумаВПН — точка входа. Запуск: python bot.py"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.types import MenuButtonWebApp, WebAppInfo

import config
import db
from handlers_admin import router as admin_router
from handlers_user import router as user_router


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    if not config.BOT_TOKEN:
        raise SystemExit("Заполните BOT_TOKEN в файле .env (образец — .env.example)")

    db.init_db()

    session = AiohttpSession(proxy=config.PROXY_URL) if config.PROXY_URL else None
    bot = Bot(
        token=config.BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_routers(admin_router, user_router)

    await bot.delete_webhook(drop_pending_updates=True)

    if config.WEBAPP_URL:
        # Синяя кнопка слева от поля ввода открывает мини-приложение
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                type="web_app",
                text="🛍 Магазин",
                web_app=WebAppInfo(url=config.WEBAPP_URL),
            )
        )
        logging.info("Мини-приложение подключено: %s", config.WEBAPP_URL)

    logging.info("Бот %s запущен", config.SERVICE_NAME)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit) as e:
        print(f"Остановлено: {e}")
