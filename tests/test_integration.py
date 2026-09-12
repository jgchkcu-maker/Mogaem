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

        await service.rate(a.id, b.id, "Chad")
        assert await service.next_candidate(a.id) is None

        await service.rate(b.id, a.id, "Chad-lite")
        request = await service.create_chat_request(b.id, a.id)
        resolved, match = await service.resolve_chat_request(request.id, a.id, accept=True)
        assert resolved.status == "accepted"
        assert match is not None
        assert {match.user_low_id, match.user_high_id} == {a.id, b.id}

    await engine.dispose()
