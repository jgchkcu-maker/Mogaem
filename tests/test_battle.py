from __future__ import annotations

import pytest


def test_elo_helpers_cover_equal_ratings_upset_k_tiers_and_floor():
    from mogaem.battle import expected_score, k_factor, updated_elo

    assert expected_score(1000, 1000) == pytest.approx(0.5)
    assert k_factor(0) == 48
    assert k_factor(9) == 48
    assert k_factor(10) == 32
    assert k_factor(49) == 32
    assert k_factor(50) == 20

    assert updated_elo(1000, 1000, 1.0, 0) == 1024
    assert updated_elo(1000, 1000, 0.0, 0) == 976

    # Beating a much stronger opponent should award more than beating an equal one.
    assert updated_elo(1000, 1400, 1.0, 0) > 1024
    # Elo is never allowed to drop below the product floor.
    assert updated_elo(100, 2000, 0.0, 100) == 100


@pytest.mark.asyncio
async def test_battle_service_issues_same_gender_pair_votes_once_and_updates_stats():
    pytest.importorskip("aiosqlite")

    from mogaem.db import build_engine, build_session_factory, init_db
    from mogaem.services import MogaemService, RequestStateError

    engine = build_engine("sqlite+aiosqlite:///:memory:")
    await init_db(engine)
    factory = build_session_factory(engine)

    async with factory() as session:
        service = MogaemService(session)
        voter = await service.ensure_user(4100, "voter")
        a = await service.ensure_user(4101, "alpha")
        b = await service.ensure_user(4102, "beta")
        woman = await service.ensure_user(4103, "gamma")

        await service.save_profile(voter.id, name="Viewer", age=20, gender="male", search_gender="any", city=None, bio="", photos=["v"])
        await service.save_profile(a.id, name="Alpha", age=21, gender="male", search_gender="any", city=None, bio="", photos=["a"])
        await service.save_profile(b.id, name="Beta", age=22, gender="male", search_gender="any", city=None, bio="", photos=["b"])
        await service.save_profile(woman.id, name="Gamma", age=23, gender="female", search_gender="any", city=None, bio="", photos=["g"])

        battle = await service.next_battle(voter.id)
        assert battle is not None
        assert {battle.left.user_id, battle.right.user_id} == {a.id, b.id}
        assert battle.left.gender == battle.right.gender == "male"
        assert voter.id not in {battle.left.user_id, battle.right.user_id}

        result = await service.resolve_battle(battle.battle_id, voter.id, battle.left.user_id)
        assert result.winner.user_id == battle.left.user_id
        assert result.loser.user_id == battle.right.user_id
        assert result.winner.elo > 1000
        assert result.loser.elo < 1000
        assert result.winner.battles == 1
        assert result.winner.wins == 1
        assert result.loser.losses == 1

        # Repeating the identical result is idempotent and must not mutate Elo twice.
        repeated = await service.resolve_battle(battle.battle_id, voter.id, battle.left.user_id)
        assert repeated.winner.elo == result.winner.elo
        assert repeated.loser.elo == result.loser.elo
        assert repeated.winner.battles == 1

        with pytest.raises(RequestStateError):
            await service.resolve_battle(battle.battle_id, voter.id, battle.right.user_id)

        # This voter has exhausted the only eligible male-vs-male pair.
        assert await service.next_battle(voter.id) is None

    await engine.dispose()


@pytest.mark.asyncio
async def test_battle_leaderboard_marks_calibration_and_orders_by_elo():
    pytest.importorskip("aiosqlite")

    from mogaem.db import build_engine, build_session_factory, init_db
    from mogaem.models import BattleRating
    from mogaem.services import MogaemService

    engine = build_engine("sqlite+aiosqlite:///:memory:")
    await init_db(engine)
    factory = build_session_factory(engine)

    async with factory() as session:
        service = MogaemService(session)
        a = await service.ensure_user(4201, "a")
        b = await service.ensure_user(4202, "b")
        await service.save_profile(a.id, name="Alpha", age=20, gender="male", search_gender="any", city=None, bio="", photos=["a"])
        await service.save_profile(b.id, name="Beta", age=20, gender="male", search_gender="any", city=None, bio="", photos=["b"])
        session.add(BattleRating(user_id=a.id, elo=1300, battles=12, wins=8, losses=4))
        session.add(BattleRating(user_id=b.id, elo=1200, battles=3, wins=2, losses=1))
        await session.commit()

        board = await service.leaderboard("male")
        assert [entry.user_id for entry in board] == [a.id, b.id]
        assert board[0].rank == 1
        assert board[0].calibrating is False
        assert board[1].rank is None
        assert board[1].calibrating is True

    await engine.dispose()
