import pytest


def test_full_bot_module_imports_with_runtime_dependencies():
    pytest.importorskip("aiogram")
    import mogaem.bot  # noqa: F401


@pytest.mark.asyncio
async def test_database_service_flow_end_to_end():
    pytest.importorskip("aiosqlite")

    from mogaem.db import build_engine, build_session_factory, init_db
    from mogaem.services import MogaemService

    engine = build_engine("sqlite+aiosqlite:///:memory:")
    await init_db(engine)
    factory = build_session_factory(engine)

    async with factory() as session:
        service = MogaemService(session)
        a = await service.ensure_user(1001, "alpha")
        b = await service.ensure_user(1002, "beta")
        await service.save_profile(a.id, name="Alpha", age=20, gender="male", search_gender="female", city=None, bio="A", photos=["file-a"])
        await service.save_profile(b.id, name="Beta", age=21, gender="female", search_gender="male", city="Krasnoyarsk", bio="B", photos=["file-b"])

        candidate = await service.next_candidate(a.id)
        assert candidate is not None
        assert candidate.user_id == b.id

        await service.rate(a.id, b.id, "9")
        assert await service.next_candidate(a.id) is None

        await service.rate(b.id, a.id, "8")
        request = await service.create_chat_request(b.id, a.id)
        resolved, match = await service.resolve_chat_request(request.id, a.id, accept=True)
        assert resolved.status == "accepted"
        assert match is not None
        assert {match.user_low_id, match.user_high_id} == {a.id, b.id}

    await engine.dispose()


def test_onboarding_uses_reply_keyboards_with_expected_rows():
    pytest.importorskip("aiogram")

    from mogaem.keyboards import reply_keyboard
    from mogaem.onboarding import CONFIRM_ROWS, GENDER_ROWS, SEARCH_GENDER_ROWS, START_ROWS

    for rows in (START_ROWS, GENDER_ROWS, SEARCH_GENDER_ROWS, CONFIRM_ROWS):
        markup = reply_keyboard(rows)
        assert [[button.text for button in row] for row in markup.keyboard] == [list(row) for row in rows]
        assert markup.resize_keyboard is True
        assert markup.is_persistent is True


def test_profile_fsm_matches_registration_order():
    pytest.importorskip("aiogram")

    from mogaem.states import ProfileForm

    names = [state.state.rsplit(":", 1)[-1] for state in ProfileForm.__all_states__]
    assert names == ["ready", "age", "gender", "search_gender", "city", "name", "bio", "photos", "preview"]
