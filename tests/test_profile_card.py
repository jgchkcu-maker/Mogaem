import pytest

from mogaem.render import profile_card_caption


def test_profile_card_caption_matches_requested_layout():
    caption = profile_card_caption(
        name="Никита",
        age=18,
        gender="male",
        search_gender="female",
        city=None,
        rating_average=9.1,
        rating_count=63,
    )

    assert caption == (
        "☘️Имя: Никита, 18 лет\n\n"
        "💘Подарили валентинок: 0\n"
        "⭐️Ваше фото оценили на: 9.1/10\n"
        "👥Вас оценили 63 человек\n\n"
        "Ваш пол: 👨мужской\n"
        "Кого вы хотите оценивать: 👩женский\n"
        "Кем вы хотите быть оценены: 🤷неважно\n\n"
        "🌇Город: Не указан"
    )


@pytest.mark.asyncio
async def test_profile_view_aggregates_received_mog_ratings():
    pytest.importorskip("aiosqlite")

    from mogaem.db import build_engine, build_session_factory, init_db
    from mogaem.services import MogaemService

    engine = build_engine("sqlite+aiosqlite:///:memory:")
    await init_db(engine)
    factory = build_session_factory(engine)

    async with factory() as session:
        service = MogaemService(session)
        target = await service.ensure_user(2001, "target")
        rater_a = await service.ensure_user(2002, "a")
        rater_b = await service.ensure_user(2003, "b")
        rater_c = await service.ensure_user(2004, "c")

        await service.save_profile(target.id, name="Никита", age=18, gender="male", search_gender="female", city=None, bio="", photos=["target-photo"])
        await service.save_profile(rater_a.id, name="A", age=19, gender="female", search_gender="any", city=None, bio="", photos=["a-photo"])
        await service.save_profile(rater_b.id, name="B", age=20, gender="female", search_gender="any", city=None, bio="", photos=["b-photo"])
        await service.save_profile(rater_c.id, name="C", age=21, gender="male", search_gender="any", city=None, bio="", photos=["c-photo"])

        await service.rate(rater_a.id, target.id, "Chad")
        await service.rate(rater_b.id, target.id, "Chad-lite")
        await service.rate(rater_c.id, target.id, "Normie")

        view = await service.profile_view(target.id)
        assert view.rating_count == 3
        assert view.rating_average == 8.0

    await engine.dispose()
