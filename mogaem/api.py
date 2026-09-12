import io
import mimetypes
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, AsyncIterator

from aiogram import Bot
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from .config import Settings
from .db import build_engine, build_session_factory, init_db
from .domain import DuplicateRatingError
from .models import Photo
from .services import MogaemService, NotFoundError, RequestStateError
from .webapp_auth import ExpiredInitData, InvalidInitData, TelegramWebAppUser, validate_init_data


class BattleVotePayload(BaseModel):
    winner_id: int


class RatingPayload(BaseModel):
    score: int = Field(ge=1, le=10)


def _profile_json(profile) -> dict:
    return {
        "user_id": profile.user_id,
        "name": profile.name,
        "age": profile.age,
        "gender": profile.gender,
        "search_gender": profile.search_gender,
        "city": profile.city,
        "bio": profile.bio,
        "photo_count": len(profile.photos),
    }


def _battle_player_json(player) -> dict:
    return {
        "user_id": player.user_id,
        "name": player.name,
        "age": player.age,
        "gender": player.gender,
        "city": player.city,
        "elo": player.elo,
        "battles": player.battles,
        "wins": player.wins,
        "losses": player.losses,
        "calibrating": player.calibrating,
        "photo_count": len(player.photos),
    }


def create_app(
    *,
    settings: Settings | None = None,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    actor_override: TelegramWebAppUser | None = None,
    dist_dir: str | Path | None = None,
) -> FastAPI:
    managed_engine: AsyncEngine | None = None

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        nonlocal managed_engine
        if app.state.settings is None:
            app.state.settings = Settings()
        if app.state.session_factory is None:
            managed_engine = build_engine(app.state.settings.async_database_url)
            await init_db(managed_engine)
            app.state.session_factory = build_session_factory(managed_engine)
        try:
            yield
        finally:
            if managed_engine is not None:
                await managed_engine.dispose()

    app = FastAPI(title="Mogaem Mini App API", version="0.2.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.actor_override = actor_override

    async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
        factory = request.app.state.session_factory
        if factory is None:
            raise HTTPException(status_code=503, detail="database is not ready")
        async with factory() as session:
            yield session

    async def get_actor(
        request: Request,
        authorization: Annotated[str | None, Header()] = None,
    ) -> TelegramWebAppUser:
        override = request.app.state.actor_override
        if override is not None:
            return override
        current_settings: Settings | None = request.app.state.settings
        if current_settings is None:
            raise HTTPException(status_code=503, detail="application settings are not ready")
        if not authorization or not authorization.startswith("tma "):
            raise HTTPException(status_code=401, detail="Telegram Mini App authorization is required")
        init_data = authorization[4:]
        try:
            return validate_init_data(
                init_data,
                current_settings.bot_token,
                max_age_seconds=current_settings.webapp_auth_max_age_seconds,
            )
        except ExpiredInitData as exc:
            raise HTTPException(status_code=401, detail="Telegram authorization has expired") from exc
        except InvalidInitData as exc:
            raise HTTPException(status_code=401, detail="Invalid Telegram Mini App authorization") from exc

    async def current_user_id(
        actor: Annotated[TelegramWebAppUser, Depends(get_actor)],
        session: Annotated[AsyncSession, Depends(get_session)],
    ) -> int:
        service = MogaemService(session)
        user = await service.ensure_user(actor.telegram_id, actor.username)
        if not await service.profile_complete(user.id):
            raise HTTPException(status_code=409, detail="Create or enable your profile in the bot first")
        return user.id

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.get("/api/me")
    async def me(
        user_id: Annotated[int, Depends(current_user_id)],
        session: Annotated[AsyncSession, Depends(get_session)],
    ) -> dict:
        service = MogaemService(session)
        profile = await service.profile_view(user_id)
        battle = await service.battle_stats(user_id)
        return {
            "profile": _profile_json(profile),
            "mog": {"average": profile.rating_average, "count": profile.rating_count},
            "battle": _battle_player_json(battle),
        }

    @app.get("/api/battle/next")
    async def next_battle(
        user_id: Annotated[int, Depends(current_user_id)],
        session: Annotated[AsyncSession, Depends(get_session)],
    ):
        service = MogaemService(session)
        battle = await service.next_battle(user_id)
        if battle is None:
            return Response(status_code=204)
        return {
            "battle_id": battle.battle_id,
            "left": _battle_player_json(battle.left),
            "right": _battle_player_json(battle.right),
        }

    @app.post("/api/battle/{battle_id}/vote")
    async def vote_battle(
        battle_id: str,
        payload: BattleVotePayload,
        user_id: Annotated[int, Depends(current_user_id)],
        session: Annotated[AsyncSession, Depends(get_session)],
    ) -> dict:
        service = MogaemService(session)
        try:
            result = await service.resolve_battle(battle_id, user_id, payload.winner_id)
        except NotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except RequestStateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {
            "battle_id": result.battle_id,
            "winner": _battle_player_json(result.winner),
            "loser": _battle_player_json(result.loser),
        }

    @app.get("/api/leaderboard")
    async def leaderboard(
        user_id: Annotated[int, Depends(current_user_id)],
        session: Annotated[AsyncSession, Depends(get_session)],
        gender: str = "any",
    ) -> dict:
        del user_id
        service = MogaemService(session)
        try:
            entries = await service.leaderboard(gender)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {"entries": [asdict(entry) for entry in entries]}

    @app.get("/api/rate/next")
    async def next_rating_candidate(
        user_id: Annotated[int, Depends(current_user_id)],
        session: Annotated[AsyncSession, Depends(get_session)],
    ):
        service = MogaemService(session)
        candidate = await service.next_candidate(user_id)
        if candidate is None:
            return Response(status_code=204)
        return {
            "profile": _profile_json(candidate),
            "mog": {"average": candidate.rating_average, "count": candidate.rating_count},
        }

    @app.post("/api/rate/{target_id}")
    async def rate_profile(
        target_id: int,
        payload: RatingPayload,
        user_id: Annotated[int, Depends(current_user_id)],
        session: Annotated[AsyncSession, Depends(get_session)],
    ) -> dict:
        service = MogaemService(session)
        target = await service.user_by_id(target_id)
        if target is None:
            raise HTTPException(status_code=404, detail="profile not found")
        try:
            await service.rate(user_id, target_id, str(payload.score))
        except DuplicateRatingError as exc:
            raise HTTPException(status_code=409, detail="You already rated this profile") from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {"target_id": target_id, "score": payload.score}

    @app.get("/api/matches")
    async def matches(
        user_id: Annotated[int, Depends(current_user_id)],
        session: Annotated[AsyncSession, Depends(get_session)],
    ) -> dict:
        service = MogaemService(session)
        rows = await service.list_matches(user_id)
        items = []
        for row in rows:
            contact_url = f"https://t.me/{row.username.lstrip('@')}" if row.username else f"tg://user?id={row.telegram_id}"
            items.append({
                "user_id": row.user_id,
                "name": row.name,
                "age": row.age,
                "city": row.city,
                "contact_url": contact_url,
                "created_at": row.created_at.isoformat(),
            })
        return {"matches": items}

    @app.get("/api/profiles/{target_id}/photo/{position}")
    async def profile_photo(
        target_id: int,
        position: int,
        user_id: Annotated[int, Depends(current_user_id)],
        session: Annotated[AsyncSession, Depends(get_session)],
        request: Request,
    ) -> Response:
        del user_id
        if position < 0 or position > 2:
            raise HTTPException(status_code=404, detail="photo not found")
        file_id = await session.scalar(select(Photo.file_id).where(Photo.user_id == target_id, Photo.position == position))
        if file_id is None:
            raise HTTPException(status_code=404, detail="photo not found")
        current_settings: Settings | None = request.app.state.settings
        if current_settings is None:
            raise HTTPException(status_code=503, detail="application settings are not ready")
        bot = Bot(current_settings.bot_token)
        try:
            tg_file = await bot.get_file(file_id)
            if not tg_file.file_path:
                raise HTTPException(status_code=502, detail="Telegram did not return a file path")
            destination = io.BytesIO()
            await bot.download_file(tg_file.file_path, destination=destination)
            media_type = mimetypes.guess_type(tg_file.file_path)[0] or "image/jpeg"
            return Response(content=destination.getvalue(), media_type=media_type, headers={"Cache-Control": "private, max-age=300"})
        finally:
            await bot.session.close()

    resolved_dist = Path(dist_dir) if dist_dir is not None else Path(__file__).resolve().parents[1] / "webapp" / "dist"
    index_file = resolved_dist / "index.html"
    assets_dir = resolved_dist / "assets"
    if index_file.is_file():
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="miniapp-assets")

        @app.get("/", include_in_schema=False)
        async def miniapp_index() -> FileResponse:
            return FileResponse(index_file)

        @app.get("/{path:path}", include_in_schema=False)
        async def miniapp_fallback(path: str):
            if path.startswith("api/") or path == "health":
                raise HTTPException(status_code=404, detail="not found")
            return FileResponse(index_file)

    return app


app = create_app()
