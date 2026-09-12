from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

RATING_CODES = {"c": "Chad", "cl": "Chad-lite", "n": "Normie", "s5": "Sub5", "s3": "Sub3"}
RATING_BUTTONS = [("🗿 Чад", "c"), ("🔥 Чад лайт", "cl"), ("🙂 Норми", "n"), ("🥀 Саб5", "s5"), ("💀 Саб3", "s3")]


def main_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🔥 Смотреть анкеты", callback_data="browse")
    kb.button(text="👤 Моя анкета", callback_data="profile:me")
    kb.button(text="⚙️ Пол поиска", callback_data="search:menu")
    kb.adjust(1)
    return kb.as_markup()


def gender_keyboard(prefix: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="👨 Муж", callback_data=f"{prefix}:male")
    kb.button(text="👩 Жен", callback_data=f"{prefix}:female")
    kb.adjust(2)
    return kb.as_markup()


def search_gender_keyboard(prefix: str = "search:set") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="👨 Муж", callback_data=f"{prefix}:male")
    kb.button(text="👩 Жен", callback_data=f"{prefix}:female")
    kb.button(text="🌐 Не важно", callback_data=f"{prefix}:any")
    kb.adjust(2, 1)
    return kb.as_markup()


def city_skip_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Пропустить", callback_data="onb:city:skip")
    return kb.as_markup()


def photo_done_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Готово", callback_data="onb:photos:done")
    return kb.as_markup()


def rating_keyboard(target_user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for text, code in RATING_BUTTONS:
        kb.button(text=text, callback_data=f"rate:{target_user_id}:{code}")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def after_rating_keyboard(target_user_id: int, reciprocal: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if reciprocal:
        kb.button(text="💬 Отправить запрос на переписку", callback_data=f"chatreq:{target_user_id}")
    kb.button(text="➡️ Следующая анкета", callback_data="browse")
    kb.adjust(1)
    return kb.as_markup()


def request_decision_keyboard(request_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Принять", callback_data=f"req:accept:{request_id}")
    kb.button(text="❌ Отклонить", callback_data=f"req:decline:{request_id}")
    kb.adjust(2)
    return kb.as_markup()


def my_profile_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🔥 Смотреть анкеты", callback_data="browse")
    kb.button(text="⚙️ Пол поиска", callback_data="search:menu")
    kb.button(text="✏️ Пересоздать анкету", callback_data="profile:recreate")
    kb.adjust(1)
    return kb.as_markup()
