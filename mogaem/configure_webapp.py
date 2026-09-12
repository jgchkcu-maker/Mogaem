from __future__ import annotations

import asyncio
import sys
from urllib.parse import urlparse

from aiogram import Bot
from aiogram.types import MenuButtonWebApp, WebAppInfo

from .config import Settings


def validate_webapp_url(url: str) -> str:
    candidate = url.strip().rstrip("/")
    parsed = urlparse(candidate)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("Mini App URL must be a valid HTTPS URL")
    return candidate


def menu_button_for_url(url: str) -> MenuButtonWebApp:
    checked = validate_webapp_url(url)
    return MenuButtonWebApp(text="⚔️ Mogaem", web_app=WebAppInfo(url=checked))


async def configure(url: str) -> None:
    settings = Settings()
    bot = Bot(settings.bot_token)
    try:
        await bot.set_chat_menu_button(menu_button=menu_button_for_url(url))
    finally:
        await bot.session.close()


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m mogaem.configure_webapp https://example.com")
    asyncio.run(configure(sys.argv[1]))


if __name__ == "__main__":
    main()
