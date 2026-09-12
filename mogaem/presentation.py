from __future__ import annotations

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup

from .render import profile_card_caption
from .services import ProfileView


async def send_profile_card(
    bot: Bot,
    chat_id: int,
    profile: ProfileView,
    *,
    reply_markup: InlineKeyboardMarkup | None = None,
    prefix: str = "",
) -> None:
    caption = prefix + profile_card_caption(
        name=profile.name,
        age=profile.age,
        gender=profile.gender,
        search_gender=profile.search_gender,
        city=profile.city,
        rating_average=profile.rating_average,
        rating_count=profile.rating_count,
    )
    if profile.photos:
        await bot.send_photo(chat_id=chat_id, photo=profile.photos[0], caption=caption, reply_markup=reply_markup)
        if len(profile.photos) > 1:
            for extra in profile.photos[1:]:
                await bot.send_photo(chat_id=chat_id, photo=extra)
    else:
        await bot.send_message(chat_id=chat_id, text=caption, reply_markup=reply_markup)
