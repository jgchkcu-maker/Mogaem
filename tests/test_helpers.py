from mogaem.config import normalize_database_url
from mogaem.render import contact_html, profile_caption, rating_summary


def test_normalize_postgres_url_for_asyncpg():
    assert normalize_database_url("postgresql://u:p@host/db") == "postgresql+asyncpg://u:p@host/db"
    assert normalize_database_url("postgres://u:p@host/db") == "postgresql+asyncpg://u:p@host/db"


def test_sqlite_url_is_unchanged():
    url = "sqlite+aiosqlite:///mogaem.db"
    assert normalize_database_url(url) == url


def test_profile_caption_handles_missing_city():
    text = profile_caption(name="Nikita", age=19, city=None, bio="Привет", gender="male")
    assert "Nikita, 19" in text
    assert "Город" not in text
    assert "Привет" in text


def test_rating_summary_has_both_directions():
    text = rating_summary(other_name="Alex", they_gave="Chad", you_gave="Sub5")
    assert "Alex" in text
    assert "Чад" in text
    assert "Саб5" in text


def test_contact_html_prefers_username_and_escapes_name():
    assert contact_html("A&B", "@alex", 123) == '<a href="https://t.me/alex">A&amp;B</a>'
    assert 'tg://user?id=123' in contact_html("Alex", None, 123)
