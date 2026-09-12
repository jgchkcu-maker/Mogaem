from __future__ import annotations

import random
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import combinations

from sqlalchemy import and_, delete, exists, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .battle import updated_elo
from .domain import DuplicateChatRequestError, DuplicateRatingError, ReciprocalRatingRequired, RATING_LABELS, RATING_SCORES, validate_profile
from .models import Battle, BattleRating, ChatRequest, Match, Photo, Profile, Rating, User


class NotFoundError(LookupError):
    pass


class RequestStateError(ValueError):
    pass


@dataclass(slots=True)
class ProfileView:
    user_id: int
    telegram_id: int
    username: str | None
    name: str
    age: int
    gender: str
    search_gender: str
    city: str | None
    bio: str
    photos: list[str]
    rating_average: float = 0.0
    rating_count: int = 0


@dataclass(slots=True)
class BattlePlayerView:
    user_id: int
    name: str
    age: int
    gender: str
    city: str | None
    photos: list[str]
    elo: int
    battles: int
    wins: int
    losses: int
    calibrating: bool


@dataclass(slots=True)
class BattleView:
    battle_id: str
    left: BattlePlayerView
    right: BattlePlayerView


@dataclass(slots=True)
class BattleResultView:
    battle_id: str
    winner: BattlePlayerView
    loser: BattlePlayerView


@dataclass(slots=True)
class LeaderboardEntry:
    user_id: int
    name: str
    age: int
    gender: str
    city: str | None
    elo: int
    battles: int
    wins: int
    losses: int
    calibrating: bool
    rank: int | None
    percentile: float | None


@dataclass(slots=True)
class MatchView:
    user_id: int
    telegram_id: int
    username: str | None
    name: str
    age: int
    city: str | None
    created_at: datetime


class MogaemService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def ensure_user(self, telegram_id: int, username: str | None) -> User:
        user = await self.session.scalar(select(User).where(User.telegram_id == telegram_id))
        if user is None:
            user = User(telegram_id=telegram_id, username=username)
            self.session.add(user)
            await self.session.flush()
        elif user.username != username:
            user.username = username
        await self.session.commit()
        return user

    async def user_by_telegram(self, telegram_id: int) -> User | None:
        return await self.session.scalar(select(User).where(User.telegram_id == telegram_id))

    async def user_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def profile_state(self, user_id: int) -> str:
        profile = await self.session.get(Profile, user_id)
        if profile is None:
            return "missing"
        return "active" if profile.is_active else "inactive"

    async def set_profile_active(self, user_id: int, active: bool) -> None:
        profile = await self.session.get(Profile, user_id)
        if profile is None:
            raise NotFoundError("profile not found")
        if active:
            photo_exists = await self.session.scalar(select(exists().where(Photo.user_id == user_id)))
            if not photo_exists:
                raise ValueError("profile requires photo")
        profile.is_active = active
        await self.session.commit()

    async def profile_complete(self, user_id: int) -> bool:
        profile = await self.session.get(Profile, user_id)
        if profile is None or not profile.is_active:
            return False
        photo_exists = await self.session.scalar(select(exists().where(Photo.user_id == user_id)))
        return bool(photo_exists)

    async def save_profile(self, user_id: int, *, name: str, age: int, gender: str, search_gender: str, city: str | None, bio: str, photos: list[str]) -> ProfileView:
        clean = validate_profile(name=name, age=age, gender=gender, search_gender=search_gender, city=city, bio=bio)
        if not photos or len(photos) > 3:
            raise ValueError("profile requires 1-3 photos")
        profile = await self.session.get(Profile, user_id)
        if profile is None:
            profile = Profile(user_id=user_id, **clean)
            self.session.add(profile)
        else:
            for key, value in clean.items():
                setattr(profile, key, value)
            profile.is_active = True
        await self.session.execute(delete(Photo).where(Photo.user_id == user_id))
        for position, file_id in enumerate(photos[:3]):
            self.session.add(Photo(user_id=user_id, file_id=file_id, position=position))
        await self.session.commit()
        return await self.profile_view(user_id)

    async def set_search_gender(self, user_id: int, value: str) -> None:
        if value not in {"male", "female", "any"}:
            raise ValueError("invalid search gender")
        profile = await self.session.get(Profile, user_id)
        if profile is None:
            raise NotFoundError("profile not found")
        profile.search_gender = value
        await self.session.commit()

    async def rating_stats(self, user_id: int) -> tuple[float, int]:
        labels = list((await self.session.scalars(select(Rating.label).where(Rating.rated_id == user_id))).all())
        scores = [RATING_SCORES[label] for label in labels if label in RATING_SCORES]
        if not scores:
            return 0.0, 0
        return round(sum(scores) / len(scores), 1), len(scores)

    async def profile_view(self, user_id: int) -> ProfileView:
        profile = await self.session.get(Profile, user_id)
        user = await self.session.get(User, user_id)
        if profile is None or user is None:
            raise NotFoundError("profile not found")
        photos = list((await self.session.scalars(select(Photo.file_id).where(Photo.user_id == user_id).order_by(Photo.position))).all())
        rating_average, rating_count = await self.rating_stats(user_id)
        return ProfileView(
            user_id=user_id,
            telegram_id=user.telegram_id,
            username=user.username,
            name=profile.name,
            age=profile.age,
            gender=profile.gender,
            search_gender=profile.search_gender,
            city=profile.city,
            bio=profile.bio,
            photos=photos,
            rating_average=rating_average,
            rating_count=rating_count,
        )

    async def next_candidate(self, viewer_id: int) -> ProfileView | None:
        viewer = await self.session.get(Profile, viewer_id)
        if viewer is None:
            raise NotFoundError("viewer profile not found")
        rated_ids = select(Rating.rated_id).where(Rating.rater_id == viewer_id)
        filters = [
            Profile.is_active.is_(True),
            Profile.user_id != viewer_id,
            Profile.user_id.not_in(rated_ids),
            exists(select(Photo.id).where(Photo.user_id == Profile.user_id)),
        ]
        if viewer.search_gender != "any":
            filters.append(Profile.gender == viewer.search_gender)
        candidate_id = await self.session.scalar(select(Profile.user_id).where(*filters).order_by(func.random()).limit(1))
        if candidate_id is None:
            return None
        return await self.profile_view(candidate_id)

    async def rating(self, rater_id: int, rated_id: int) -> Rating | None:
        return await self.session.scalar(select(Rating).where(Rating.rater_id == rater_id, Rating.rated_id == rated_id))

    async def rate(self, rater_id: int, rated_id: int, label: str) -> Rating:
        if label not in RATING_LABELS:
            raise ValueError("invalid rating")
        if rater_id == rated_id:
            raise ValueError("cannot rate self")
        if await self.rating(rater_id, rated_id):
            raise DuplicateRatingError("rating already exists")
        row = Rating(rater_id=rater_id, rated_id=rated_id, label=label)
        self.session.add(row)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise DuplicateRatingError("rating already exists") from exc
        return row

    async def _ensure_battle_rating(self, user_id: int) -> BattleRating:
        row = await self.session.get(BattleRating, user_id)
        if row is None:
            row = BattleRating(user_id=user_id, elo=1000, battles=0, wins=0, losses=0)
            self.session.add(row)
            await self.session.flush()
        return row

    async def battle_rating(self, user_id: int) -> BattlePlayerView:
        rating = await self._ensure_battle_rating(user_id)
        await self.session.commit()
        return await self._battle_player_view(user_id, rating)

    async def _battle_player_view(self, user_id: int, rating: BattleRating | None = None) -> BattlePlayerView:
        profile = await self.profile_view(user_id)
        if rating is None:
            rating = await self._ensure_battle_rating(user_id)
        return BattlePlayerView(
            user_id=user_id,
            name=profile.name,
            age=profile.age,
            gender=profile.gender,
            city=profile.city,
            photos=profile.photos,
            elo=rating.elo,
            battles=rating.battles,
            wins=rating.wins,
            losses=rating.losses,
            calibrating=rating.battles < 10,
        )

    async def next_battle(self, voter_id: int) -> BattleView | None:
        voter = await self.session.get(Profile, voter_id)
        if voter is None or not voter.is_active:
            raise NotFoundError("voter profile not found")

        eligible_rows = list((await self.session.execute(
            select(Profile.user_id, Profile.gender).where(
                Profile.is_active.is_(True),
                Profile.user_id != voter_id,
                exists(select(Photo.id).where(Photo.user_id == Profile.user_id)),
            )
        )).all())
        if len(eligible_rows) < 2:
            return None

        by_gender: dict[str, list[int]] = {}
        for user_id, gender in eligible_rows:
            by_gender.setdefault(gender, []).append(user_id)

        seen_pairs = set((await self.session.execute(
            select(Battle.pair_low_id, Battle.pair_high_id).where(Battle.voter_id == voter_id)
        )).all())

        rating_by_user: dict[int, BattleRating] = {}
        for user_id, _ in eligible_rows:
            rating_by_user[user_id] = await self._ensure_battle_rating(user_id)
        await self.session.flush()

        options: list[tuple[int, float, int, int]] = []
        for members in by_gender.values():
            for first, second in combinations(members, 2):
                low, high = sorted((first, second))
                if (low, high) in seen_pairs:
                    continue
                distance = abs(rating_by_user[first].elo - rating_by_user[second].elo)
                options.append((distance, random.random(), first, second))

        if not options:
            await self.session.commit()
            return None

        _, _, first, second = min(options, key=lambda item: (item[0], item[1]))
        if random.random() < 0.5:
            left_id, right_id = first, second
        else:
            left_id, right_id = second, first
        low, high = sorted((left_id, right_id))

        battle = Battle(
            id=secrets.token_hex(12),
            voter_id=voter_id,
            left_id=left_id,
            right_id=right_id,
            pair_low_id=low,
            pair_high_id=high,
        )
        self.session.add(battle)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            return await self.next_battle(voter_id)

        return BattleView(
            battle_id=battle.id,
            left=await self._battle_player_view(left_id),
            right=await self._battle_player_view(right_id),
        )

    async def resolve_battle(self, battle_id: str, voter_id: int, winner_id: int) -> BattleResultView:
        battle = await self.session.get(Battle, battle_id)
        if battle is None:
            raise NotFoundError("battle not found")
        if battle.voter_id != voter_id:
            raise RequestStateError("battle belongs to another voter")
        if winner_id not in {battle.left_id, battle.right_id}:
            raise RequestStateError("winner is not part of this battle")

        if battle.winner_id is not None:
            if battle.winner_id != winner_id:
                raise RequestStateError("battle was already resolved with another winner")
            loser_id = battle.loser_id
            if loser_id is None:
                raise RequestStateError("battle result is incomplete")
            return BattleResultView(
                battle_id=battle.id,
                winner=await self._battle_player_view(winner_id),
                loser=await self._battle_player_view(loser_id),
            )

        loser_id = battle.right_id if winner_id == battle.left_id else battle.left_id
        winner_rating = await self._ensure_battle_rating(winner_id)
        loser_rating = await self._ensure_battle_rating(loser_id)

        winner_before = winner_rating.elo
        loser_before = loser_rating.elo
        winner_after = updated_elo(winner_before, loser_before, 1.0, winner_rating.battles)
        loser_after = updated_elo(loser_before, winner_before, 0.0, loser_rating.battles)

        winner_rating.elo = winner_after
        winner_rating.battles += 1
        winner_rating.wins += 1
        loser_rating.elo = loser_after
        loser_rating.battles += 1
        loser_rating.losses += 1

        battle.winner_id = winner_id
        battle.loser_id = loser_id
        battle.winner_elo_before = winner_before
        battle.winner_elo_after = winner_after
        battle.loser_elo_before = loser_before
        battle.loser_elo_after = loser_after
        battle.resolved_at = datetime.now(timezone.utc)
        await self.session.commit()

        return BattleResultView(
            battle_id=battle.id,
            winner=await self._battle_player_view(winner_id, winner_rating),
            loser=await self._battle_player_view(loser_id, loser_rating),
        )

    async def battle_stats(self, user_id: int) -> BattlePlayerView:
        rating = await self._ensure_battle_rating(user_id)
        await self.session.commit()
        return await self._battle_player_view(user_id, rating)

    async def leaderboard(self, gender: str = "any") -> list[LeaderboardEntry]:
        if gender not in {"any", "male", "female"}:
            raise ValueError("invalid leaderboard gender")
        filters = [
            Profile.is_active.is_(True),
            exists(select(Photo.id).where(Photo.user_id == Profile.user_id)),
        ]
        if gender != "any":
            filters.append(Profile.gender == gender)
        profile_rows = list((await self.session.execute(
            select(Profile.user_id, Profile.name, Profile.age, Profile.gender, Profile.city).where(*filters)
        )).all())

        ratings: dict[int, BattleRating] = {}
        for row in profile_rows:
            ratings[row.user_id] = await self._ensure_battle_rating(row.user_id)
        await self.session.commit()

        profile_rows.sort(key=lambda row: (-ratings[row.user_id].elo, -ratings[row.user_id].battles, row.user_id))
        calibrated_total = sum(1 for row in profile_rows if ratings[row.user_id].battles >= 10)
        calibrated_rank = 0
        entries: list[LeaderboardEntry] = []
        for row in profile_rows:
            rating = ratings[row.user_id]
            calibrating = rating.battles < 10
            rank = None
            percentile = None
            if not calibrating:
                calibrated_rank += 1
                rank = calibrated_rank
                if calibrated_total:
                    percentile = round(100.0 * (calibrated_total - rank + 1) / calibrated_total, 1)
            entries.append(LeaderboardEntry(
                user_id=row.user_id,
                name=row.name,
                age=row.age,
                gender=row.gender,
                city=row.city,
                elo=rating.elo,
                battles=rating.battles,
                wins=rating.wins,
                losses=rating.losses,
                calibrating=calibrating,
                rank=rank,
                percentile=percentile,
            ))
        return entries

    async def pair_ratings(self, user_a: int, user_b: int) -> tuple[Rating | None, Rating | None]:
        a_to_b = await self.rating(user_a, user_b)
        b_to_a = await self.rating(user_b, user_a)
        return a_to_b, b_to_a

    async def create_chat_request(self, requester_id: int, recipient_id: int) -> ChatRequest:
        a_to_b, b_to_a = await self.pair_ratings(requester_id, recipient_id)
        if a_to_b is None or b_to_a is None:
            raise ReciprocalRatingRequired("both users must rate each other")
        pending = await self.session.scalar(
            select(ChatRequest).where(
                ChatRequest.status == "pending",
                or_(
                    and_(ChatRequest.requester_id == requester_id, ChatRequest.recipient_id == recipient_id),
                    and_(ChatRequest.requester_id == recipient_id, ChatRequest.recipient_id == requester_id),
                ),
            )
        )
        if pending is not None:
            raise DuplicateChatRequestError("pending request already exists")
        row = ChatRequest(requester_id=requester_id, recipient_id=recipient_id, status="pending")
        self.session.add(row)
        await self.session.commit()
        return row

    async def resolve_chat_request(self, request_id: int, actor_id: int, *, accept: bool) -> tuple[ChatRequest, Match | None]:
        row = await self.session.get(ChatRequest, request_id)
        if row is None:
            raise NotFoundError("request not found")
        if row.recipient_id != actor_id:
            raise RequestStateError("only recipient can resolve request")
        if row.status != "pending":
            raise RequestStateError("request already resolved")
        row.status = "accepted" if accept else "declined"
        row.resolved_at = datetime.now(timezone.utc)
        match = None
        if accept:
            match = await self._get_or_create_match(row.requester_id, row.recipient_id)
        await self.session.commit()
        return row, match

    async def _get_or_create_match(self, user_a: int, user_b: int) -> Match:
        low, high = sorted((user_a, user_b))
        row = await self.session.scalar(select(Match).where(Match.user_low_id == low, Match.user_high_id == high))
        if row is None:
            row = Match(user_low_id=low, user_high_id=high)
            self.session.add(row)
            await self.session.flush()
        return row

    async def list_matches(self, user_id: int) -> list[MatchView]:
        rows = list((await self.session.scalars(select(Match).where(
            or_(Match.user_low_id == user_id, Match.user_high_id == user_id)
        ).order_by(Match.created_at.desc()))).all())
        result: list[MatchView] = []
        for match in rows:
            other_id = match.user_high_id if match.user_low_id == user_id else match.user_low_id
            user = await self.session.get(User, other_id)
            profile = await self.session.get(Profile, other_id)
            if user is None or profile is None:
                continue
            result.append(MatchView(
                user_id=other_id,
                telegram_id=user.telegram_id,
                username=user.username,
                name=profile.name,
                age=profile.age,
                city=profile.city,
                created_at=match.created_at,
            ))
        return result
