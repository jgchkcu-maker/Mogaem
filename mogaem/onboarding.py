from __future__ import annotations

ONBOARDING_STEPS = (
    "age",
    "gender",
    "search_gender",
    "city",
    "name",
    "bio",
    "photos",
    "preview",
)

START_BUTTON = "👌 Давай начнем"
MALE_BUTTON = "🙋‍♂️ Парень"
FEMALE_BUTTON = "🙋‍♀️ Девушка"
SEARCH_FEMALE_BUTTON = "👧 Девушек"
SEARCH_MALE_BUTTON = "👦 Парней"
SEARCH_ANY_BUTTON = "👥 Всех"
SKIP_BUTTON = "Пропустить"
PHOTO_DONE_BUTTON = "✅ Готово"
CONFIRM_BUTTON = "✅ Всё верно"
EDIT_BUTTON = "✏️ Изменить"

START_ROWS = ((START_BUTTON,),)
GENDER_ROWS = ((MALE_BUTTON, FEMALE_BUTTON),)
SEARCH_GENDER_ROWS = ((SEARCH_FEMALE_BUTTON, SEARCH_MALE_BUTTON), (SEARCH_ANY_BUTTON,))
SKIP_ROWS = ((SKIP_BUTTON,),)
PHOTO_DONE_ROWS = ((PHOTO_DONE_BUTTON,),)
CONFIRM_ROWS = ((CONFIRM_BUTTON,), (EDIT_BUTTON,))

INTRO_TEXT = (
    "Привет 👋\n\n"
    "Здесь можно смотреть анкеты, оценивать внешность и находить людей для общения.\n\n"
    "Сначала создадим твою анкету."
)
START_WARNING = (
    "Только один момент: используй свои настоящие данные и фото. "
    "Не выдавай себя за другого человека.\n\n"
    "Сколько тебе лет?"
)
AGE_PROMPT = "Сколько тебе лет?"
GENDER_PROMPT = "Теперь выбери свой пол 👇"
SEARCH_GENDER_PROMPT = "Кого хочешь видеть в поиске?"
CITY_PROMPT = "Из какого ты города?\n\nЕсли не хочешь указывать — нажми «Пропустить»."
NAME_PROMPT = "Как тебя зовут?"
BIO_PROMPT = "Расскажи немного о себе.\n\nЕсли не хочешь — можно пропустить."
PHOTO_PROMPT = "Теперь пришли свою фотографию 📸\n\nМожно добавить от 1 до 3 фото."
PREVIEW_PROMPT = "Так будет выглядеть твоя анкета 👇"
PREVIEW_QUESTION = "Всё верно?"

GENDER_BY_BUTTON = {
    MALE_BUTTON: "male",
    FEMALE_BUTTON: "female",
}
SEARCH_GENDER_BY_BUTTON = {
    SEARCH_FEMALE_BUTTON: "female",
    SEARCH_MALE_BUTTON: "male",
    SEARCH_ANY_BUTTON: "any",
}
