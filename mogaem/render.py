from __future__ import annotations

import html

RATING_DISPLAY = {
    "10": "10/10 — Гигачад",
    "9": "9/10 — Чад",
    "8": "8/10 — Чадлайт",
    "7": "7/10 — HTN",
    "6": "6/10 — MTN",
    "5": "5/10 — LTN",
    "4": "4/10 — Сабнорми",
    "3": "3/10 — Инцел-тир",
    "2": "2/10 — Труцел",
    "1": "1/10 — Блэкпилл-абсолют",
    # Historical values kept so old mutual ratings still render cleanly.
    "Chad": "Чад",
    "Chad-lite": "Чад лайт",
    "Normie": "Норми",
    "Sub5": "Саб5",
    "Sub3": "Саб3",
}

RATING_SCALE_TEXT = (
    "<b>Шкала MOG 1–10</b>\n\n"
    "<b>10/10 — Гигачад (Gigachad)</b>\n"
    "Недостижимый генетический абсолют. Идеальная костная структура, нулевой процент лишнего жира, абсолютная симметрия и социальный статус, который работает на автомате без единого произнесенного слова.\n\n"
    "<b>9/10 — Чад (Chad)</b>\n"
    "Эталон привлекательности в реальной жизни. Отличный рост, выраженная челюсть, уверенность по умолчанию. Общество прощает любые социальные или поведенческие ошибки просто за счет внешних данных.\n\n"
    "<b>8/10 — Чадлайт (Chadlite)</b>\n"
    "Верхний эшелон нормы с заходом в высшую лигу. База отличная (рост, пропорции лица), но требует минимальной поддержки: правильной стрижки, стиля, поддержания процента жира и осанки, чтобы держать планку.\n\n"
    "<b>7/10 — HTN (High-Tier Normie)</b>\n"
    "Твердый уровень выше среднего. Симпатичный, но без выдающейся маскулинной архитектуры лица. При грамотном стайлинге и форме легко мимикрирует под Чадлайта, но в неудачный день сливается с толпой.\n\n"
    "<b>6/10 — MTN (Mid-Tier Normie)</b>\n"
    "Истинная середина распределения. Средний рост, нейтральное лицо, отсутствие как ярких плюсов, так и критических изъянов. Все результаты в социуме зависят исключительно от кошелька, чувства юмора и софт-скиллов.\n\n"
    "<b>5/10 — LTN (Low-Tier Normie)</b>\n"
    "Чуть ниже среднего. Есть заметные минусы: слабая линия подбородка, легкая асимметрия или проблемы с осанкой. Требует ощутимых вложений в спортзал и уход за собой, чтобы просто подняться до базового MTN.\n\n"
    "<b>4/10 — Сабнорми (Sub-Normie)</b>\n"
    "Серая зона полной социальной невидимости. Противоположный пол не воспринимает как потенциального партнера без исключительных материальных или статусных компенсаций.\n\n"
    "<b>3/10 — Инцел-тир (Incel-tier)</b>\n"
    "Выраженные штрафы по генетике (сильный дефицит роста, серьезная асимметрия, неудачный прикус). Любое социальное взаимодействие дается с сильным скрипом и требует кратно больших усилий, чем у остальных.\n\n"
    "<b>2/10 — Труцел (Truecel)</b>\n"
    "Глубокий функциональный и эстетический минус. Комбинация нескольких критических дефектов внешности, где базовый уход за собой уже не спасает без вмешательства пластической хирургии и ортодонтии.\n\n"
    "<b>1/10 — Блэкпилл-абсолют (Blackpill-tier)</b>\n"
    "Статистическое дно выборки. Полная эстетическая безнадежность, используемая в сети как мем или наглядное пособие к фатализму."
)

GENDER_DISPLAY = {"male": "Мужчина", "female": "Женщина"}
CARD_GENDER_DISPLAY = {
    "male": "👨мужской",
    "female": "👩женский",
    "any": "🤷неважно",
}


def profile_caption(*, name: str, age: int, city: str | None, bio: str, gender: str) -> str:
    lines = [f"<b>{html.escape(name)}, {age}</b>", GENDER_DISPLAY.get(gender, gender)]
    if city:
        lines.append(f"📍 {html.escape(city)}")
    if bio:
        lines.extend(["", html.escape(bio)])
    return "\n".join(lines)


def profile_card_caption(
    *,
    name: str,
    age: int,
    gender: str,
    search_gender: str,
    city: str | None,
    rating_average: float,
    rating_count: int,
    valentines_received: int = 0,
    rated_by_gender: str = "any",
) -> str:
    safe_name = html.escape(name)
    safe_city = html.escape(city) if city else "Не указан"
    gender_text = CARD_GENDER_DISPLAY.get(gender, "🤷‍не указано")
    search_text = CARD_GENDER_DISPLAY.get(search_gender, "🤷неважно")
    rated_by_text = CARD_GENDER_DISPLAY.get(rated_by_gender, "🤷неважно")
    score = round(float(rating_average), 1)

    return (
        f"☘️Имя: {safe_name}, {age} лет\n\n"
        f"💘Подарили валентинок: {valentines_received}\n"
        f"⭐️Ваше фото оценили на: {score:.1f}/10\n"
        f"👥Вас оценили {rating_count} человек\n\n"
        f"Ваш пол: {gender_text}\n"
        f"Кого вы хотите оценивать: {search_text}\n"
        f"Кем вы хотите быть оценены: {rated_by_text}\n\n"
        f"🌇Город: {safe_city}"
    )


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
