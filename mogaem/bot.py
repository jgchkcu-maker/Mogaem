from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .config import Settings
from .db import build_engine, build_session_factory, init_db
from .handlers import browse_router, profile_router, requests_router


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = Settings()
    engine = build_engine(settings.async_database_url)
    session_factory = build_session_factory(engine)
    await init_db(engine)

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_routers(profile_router, browse_router, requests_router)
    try:
        await bot.delete_webhook(drop_pending_updates=False)
        await dp.start_polling(bot, session_factory=session_factory)
    finally:
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
