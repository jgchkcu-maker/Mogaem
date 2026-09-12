import pytest


@pytest.mark.asyncio
async def test_profile_lifecycle_distinguishes_missing_active_inactive_and_preserves_data():
    pytest.importorskip("aiosqlite")

    from mogaem.db import build_engine, build_session_factory, init_db
    from mogaem.services import MogaemService

    assert callable(getattr(MogaemService, "profile_state", None))
    assert callable(getattr(MogaemService, "set_profile_active", None))

    engine = build_engine("sqlite+aiosqlite:///:memory:")
    await init_db(engine)
    factory = build_session_factory(engine)

    async with factory() as session:
        service = MogaemService(session)
        target = await service.ensure_user(3001, "target")
        rater = await service.ensure_user(3002, "rater")

        assert await service.profile_state(target.id) == "missing"

        await service.save_profile(
            target.id,
            name="Никита",
            age=18,
            gender="male",
            search_gender="female",
            city="Красноярск",
            bio="",
            photos=["target-photo"],
        )
        await service.save_profile(
            rater.id,
            name="Анна",
            age=19,
            gender="female",
            search_gender="male",
            city=None,
            bio="",
            photos=["rater-photo"],
        )
        await service.rate(rater.id, target.id, "9")

        assert await service.profile_state(target.id) == "active"
        assert await service.profile_complete(target.id) is True

        await service.set_profile_active(target.id, False)
        assert await service.profile_state(target.id) == "inactive"
        assert await service.profile_complete(target.id) is False

        inactive_view = await service.profile_view(target.id)
        assert inactive_view.photos == ["target-photo"]
        assert inactive_view.rating_average == 9.0
        assert inactive_view.rating_count == 1

        await service.set_profile_active(target.id, True)
        assert await service.profile_state(target.id) == "active"
        assert await service.profile_complete(target.id) is True

    await engine.dispose()


def test_profile_lifecycle_keyboards_have_expected_actions():
    pytest.importorskip("aiogram")

    import mogaem.keyboards as keyboards

    assert callable(getattr(keyboards, "inactive_profile_keyboard", None))
    assert callable(getattr(keyboards, "profile_disable_confirm_keyboard", None))

    my_buttons = [button for row in keyboards.my_profile_keyboard().inline_keyboard for button in row]
    assert any(button.callback_data == "profile:disable" for button in my_buttons)

    inactive_buttons = [button for row in keyboards.inactive_profile_keyboard().inline_keyboard for button in row]
    assert [(button.text, button.callback_data) for button in inactive_buttons] == [
        ("❤️ Включить анкету", "profile:enable"),
        ("✏️ Создать заново", "profile:recreate"),
    ]

    confirm_buttons = [button for row in keyboards.profile_disable_confirm_keyboard().inline_keyboard for button in row]
    assert [(button.text, button.callback_data) for button in confirm_buttons] == [
        ("✅ Да, отключить", "profile:disable:confirm"),
        ("↩️ Нет", "profile:disable:cancel"),
    ]
