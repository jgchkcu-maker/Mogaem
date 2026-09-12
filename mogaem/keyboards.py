from __future__ import annotations

from collections.abc import Sequence

from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

RATING_CODES = {str(value): str(value) for value in range(10, 0, -1)}
RATING_BUTTONS = [
    ("10 Гигачад", "10"),
    ("9 Чад", "9"),
    ("8 Чадлайт", "8"),
    ("7 HTN", "7"),
    ("6 MTN", "6"),
    ("5 LTN", "5"),
    ("4 Сабнорми", "4"),
    ("3 Инцел-тир", "3"),
    ("2 Труцел", "2"),
    ("1 Блэкпилл", "1"),
]


def reply_keyboard(rows: Sequence[Sequence[str]]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text) for text in row] for row in rows],
        resize_keyboard=True,
        is_persistent=True,
    )


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


def rating_keyboard(target_user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for text, code in RATING_BUTTONS:
        kb.button(text=text, callback_data=f"rate:{target_user_id}:{code}")
    kb.button(text="ℹ️ Что значит шкала?", callback_data="rating:scale")
    kb.adjust(2, 2, 2, 2, 2, 1)
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
    kb.button(text="😴 Отключить анкету", callback_data="profile:disable")
    kb.adjust(1)
    return kb.as_markup()


def inactive_profile_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="❤️ Включить анкету", callback_data="profile:enable")
    kb.button(text="✏️ Создать заново", callback_data="profile:recreate")
    kb.adjust(1)
    return kb.as_markup()


def profile_disable_confirm_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да, отключить", callback_data="profile:disable:confirm")
    kb.button(text="↩️ Нет", callback_data="profile:disable:cancel")
    kb.adjust(1)
    return kb.as_markup()
