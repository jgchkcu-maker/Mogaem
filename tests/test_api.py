from __future__ import annotations

import httpx
import pytest


@pytest.mark.asyncio
async def test_miniapp_api_exposes_profile_battle_leaderboard_rating_and_matches():
    from mogaem.api import create_app
    from mogaem.config import Settings
    from mogaem.db import build_engine, build_session_factory, init_db
    from mogaem.services import MogaemService
    from mogaem.webapp_auth import TelegramWebAppUser

    engine = build_engine("sqlite+aiosqlite:///:memory:")
    await init_db(engine)
    factory = build_session_factory(engine)

    async with factory() as session:
        service = MogaemService(session)
        viewer = await service.ensure_user(5000, "viewer")
        alpha = await service.ensure_user(5001, "alpha")
        beta = await service.ensure_user(5002, "beta")
        gamma = await service.ensure_user(5003, "gamma")
        await service.save_profile(viewer.id, name="Viewer", age=20, gender="male", search_gender="any", city="Krasnoyarsk", bio="", photos=["viewer-photo"])
        await service.save_profile(alpha.id, name="Alpha", age=21, gender="male", search_gender="any", city=None, bio="", photos=["alpha-photo"])
        await service.save_profile(beta.id, name="Beta", age=22, gender="male", search_gender="any", city=None, bio="", photos=["beta-photo"])
        await service.save_profile(gamma.id, name="Gamma", age=23, gender="female", search_gender="any", city=None, bio="", photos=["gamma-photo"])

    settings = Settings(bot_token="123456:TEST", database_url="sqlite+aiosqlite:///:memory:")
    actor = TelegramWebAppUser(telegram_id=5000, first_name="Viewer", username="viewer")
    app = create_app(settings=settings, session_factory=factory, actor_override=actor)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        health = await client.get("/health")
        assert health.status_code == 200
        assert health.json() == {"status": "ok"}

        me = await client.get("/api/me")
        assert me.status_code == 200, me.text
        body = me.json()
        assert body["profile"]["name"] == "Viewer"
        assert body["mog"]["average"] == 0.0
        assert body["battle"]["elo"] == 1000
        assert body["battle"]["calibrating"] is True

        battle = await client.get("/api/battle/next")
        assert battle.status_code == 200, battle.text
        battle_body = battle.json()
        assert battle_body["battle_id"]
        assert {battle_body["left"]["name"], battle_body["right"]["name"]} == {"Alpha", "Beta"}

        vote = await client.post(
            f"/api/battle/{battle_body['battle_id']}/vote",
            json={"winner_id": battle_body["left"]["user_id"]},
        )
        assert vote.status_code == 200, vote.text
        vote_body = vote.json()
        assert vote_body["winner"]["elo"] > 1000
        assert vote_body["loser"]["elo"] < 1000

        board = await client.get("/api/leaderboard", params={"gender": "male"})
        assert board.status_code == 200, board.text
        names = [entry["name"] for entry in board.json()["entries"]]
        assert {"Viewer", "Alpha", "Beta"}.issubset(set(names))

        candidate = await client.get("/api/rate/next")
        assert candidate.status_code == 200, candidate.text
        candidate_body = candidate.json()
        assert candidate_body["profile"]["user_id"] != viewer.id

        rated = await client.post(
            f"/api/rate/{candidate_body['profile']['user_id']}",
            json={"score": 8},
        )
        assert rated.status_code == 200, rated.text
        assert rated.json()["score"] == 8

        matches = await client.get("/api/matches")
        assert matches.status_code == 200, matches.text
        assert matches.json() == {"matches": []}

    await engine.dispose()
