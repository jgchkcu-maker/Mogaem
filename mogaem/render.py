from __future__ import annotations

import html

RATING_DISPLAY = {
    "Chad": "Чад",
    "Chad-lite": "Чад лайт",
    "Normie": "Норми",
    "Sub5": "Саб5",
    "Sub3": "Саб3",
}
GENDER_DISPLAY = {"male": "Мужчина", "female": "Женщина"}


def profile_caption(*, name: str, age: int, city: str | None, bio: str, gender: str) -> str:
    lines = [f"<b>{html.escape(name)}, {age}</b>", GENDER_DISPLAY.get(gender, gender)]
    if city:
        lines.append(f"📍 {html.escape(city)}")
    if bio:
        lines.extend(["", html.escape(bio)])
    return "\n".join(lines)


def rating_summary(*, other_name: str, they_gave: str, you_gave: str) -> str:
    return (
        f"<b>{html.escape(other_name)}</b>\n"
        f"Оценка тебе: <b>{RATING_DISPLAY.get(they_gave, html.escape(they_gave))}</b>\n"
        f"Твоя оценка: <b>{RATING_DISPLAY.get(you_gave, html.escape(you_gave))}</b>"
    )


def contact_html(name: str, username: str | None, telegram_id: int) -> str:
    safe_name = html.escape(name)
    if username:
        safe_username = html.escape(username.lstrip("@"))
        return f'<a href="https://t.me/{safe_username}">{safe_name}</a>'
    return f'<a href="tg://user?id={telegram_id}">{safe_name}</a>'
