from mogaem.onboarding import (
    BIO_PROMPT,
    CITY_PROMPT,
    CONFIRM_ROWS,
    GENDER_ROWS,
    INTRO_TEXT,
    ONBOARDING_STEPS,
    PHOTO_DONE_ROWS,
    SEARCH_GENDER_ROWS,
    START_ROWS,
    SKIP_ROWS,
)


def test_dayvinchik_style_onboarding_order():
    assert ONBOARDING_STEPS == (
        "age",
        "gender",
        "search_gender",
        "city",
        "name",
        "bio",
        "photos",
        "preview",
    )


def test_start_has_one_wide_reply_button():
    assert START_ROWS == (("👌 Давай начнем",),)
    assert "анкет" in INTRO_TEXT.lower()


def test_gender_buttons_are_two_buttons_in_one_row():
    assert GENDER_ROWS == (("🙋‍♂️ Парень", "🙋‍♀️ Девушка"),)


def test_search_gender_layout_is_two_plus_one():
    assert SEARCH_GENDER_ROWS == (("👧 Девушек", "👦 Парней"), ("👥 Всех",))


def test_optional_text_steps_have_skip_button():
    assert SKIP_ROWS == (("Пропустить",),)
    assert "Пропустить" in CITY_PROMPT
    assert "пропустить" in BIO_PROMPT.lower()


def test_photo_and_preview_actions_are_bottom_reply_buttons():
    assert PHOTO_DONE_ROWS == (("✅ Готово",),)
    assert CONFIRM_ROWS == (("✅ Всё верно",), ("✏️ Изменить",))
