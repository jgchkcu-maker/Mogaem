import pytest

from mogaem.domain import RATING_LABELS, create_rating
from mogaem.keyboards import rating_keyboard
from mogaem.render import RATING_DISPLAY


def test_rating_labels_are_ten_point_scale():
    assert RATING_LABELS == tuple(str(value) for value in range(10, 0, -1))


def test_create_rating_accepts_numeric_level():
    ratings = {}
    row = create_rating(ratings, rater_id=1, rated_id=2, label="10")
    assert row["label"] == "10"


def test_rating_display_names_match_scale():
    assert RATING_DISPLAY["10"] == "10/10 — Гигачад"
    assert RATING_DISPLAY["9"] == "9/10 — Чад"
    assert RATING_DISPLAY["8"] == "8/10 — Чадлайт"
    assert RATING_DISPLAY["7"] == "7/10 — HTN"
    assert RATING_DISPLAY["6"] == "6/10 — MTN"
    assert RATING_DISPLAY["5"] == "5/10 — LTN"
    assert RATING_DISPLAY["4"] == "4/10 — Сабнорми"
    assert RATING_DISPLAY["3"] == "3/10 — Инцел-тир"
    assert RATING_DISPLAY["2"] == "2/10 — Труцел"
    assert RATING_DISPLAY["1"] == "1/10 — Блэкпилл-абсолют"


def test_rating_keyboard_is_five_rows_of_two_plus_info():
    markup = rating_keyboard(42)
    rows = markup.inline_keyboard
    assert [len(row) for row in rows] == [2, 2, 2, 2, 2, 1]
    assert rows[0][0].text == "10 Гигачад"
    assert rows[0][1].text == "9 Чад"
    assert rows[4][0].text == "2 Труцел"
    assert rows[4][1].text == "1 Блэкпилл"
    assert rows[5][0].text == "ℹ️ Что значит шкала?"
    assert rows[5][0].callback_data == "rating:scale"
