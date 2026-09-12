from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import and_, delete, exists, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .domain import DuplicateChatRequestError, DuplicateRatingError, ReciprocalRatingRequired, RATING_LABELS, validate_profile
from .models import ChatRequest, Match, Photo, Profile, Rating, User


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

    async def profile_view(self, user_id: int) -> ProfileView:
        profile = await self.session.get(Profile, user_id)
        user = await self.session.get(User, user_id)
        if profile is None or user is None:
            raise NotFoundError("profile not found")
        photos = list((await self.session.scalars(select(Photo.file_id).where(Photo.user_id == user_id).order_by(Photo.position))).all())
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
