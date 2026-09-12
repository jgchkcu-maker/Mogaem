from __future__ import annotations

from typing import MutableMapping, MutableSequence

RATING_LABELS = ("Chad", "Chad-lite", "Normie", "Sub5", "Sub3")
RATING_SCORES = {
    "Chad": 10.0,
    "Chad-lite": 8.0,
    "Normie": 6.0,
    "Sub5": 4.0,
    "Sub3": 2.0,
}
GENDERS = {"male", "female"}
SEARCH_GENDERS = {"male", "female", "any"}


class DuplicateRatingError(ValueError):
    pass


class ReciprocalRatingRequired(ValueError):
    pass


class DuplicateChatRequestError(ValueError):
    pass


def validate_profile(*, name: str, age: int, gender: str, search_gender: str, bio: str, city: str | None = None) -> dict:
    name = name.strip()
    bio = bio.strip()
    city = city.strip() if city and city.strip() else None
    if len(name) < 2 or len(name) > 40:
        raise ValueError("name must be 2-40 characters")
    if age < 18 or age > 99:
        raise ValueError("age must be 18-99")
    if gender not in GENDERS:
        raise ValueError("invalid gender")
    if search_gender not in SEARCH_GENDERS:
        raise ValueError("invalid search gender")
    if len(bio) > 500:
        raise ValueError("bio too long")
    if city and len(city) > 80:
        raise ValueError("city too long")
    return {
        "name": name,
        "age": age,
        "gender": gender,
        "search_gender": search_gender,
        "bio": bio,
        "city": city,
    }


def eligible_candidate(*, viewer_id: int, candidate_id: int, search_gender: str, candidate_gender: str, already_rated: bool) -> bool:
    if viewer_id == candidate_id or already_rated:
        return False
    return search_gender == "any" or search_gender == candidate_gender


def create_rating(ratings: MutableMapping[tuple[int, int], str], *, rater_id: int, rated_id: int, label: str) -> dict:
    if rater_id == rated_id:
        raise ValueError("cannot rate self")
    if label not in RATING_LABELS:
        raise ValueError("invalid rating label")
    key = (rater_id, rated_id)
    if key in ratings:
        raise DuplicateRatingError("rating already exists")
    ratings[key] = label
    return {"rater_id": rater_id, "rated_id": rated_id, "label": label}


def create_chat_request(requests: MutableSequence[dict], ratings: MutableMapping[tuple[int, int], str], *, requester_id: int, recipient_id: int) -> dict:
    if requester_id == recipient_id:
        raise ValueError("cannot request self")
    requester_rating = ratings.get((requester_id, recipient_id))
    recipient_rating = ratings.get((recipient_id, requester_id))
    if not requester_rating or not recipient_rating:
        raise ReciprocalRatingRequired("both users must rate each other")
    if any(r["requester_id"] == requester_id and r["recipient_id"] == recipient_id and r["status"] == "pending" for r in requests):
        raise DuplicateChatRequestError("pending request already exists")
    request = {
        "id": len(requests) + 1,
        "requester_id": requester_id,
        "recipient_id": recipient_id,
        "requester_rating": requester_rating,
        "recipient_rating": recipient_rating,
        "status": "pending",
    }
    requests.append(request)
    return request


def create_or_get_match(matches: MutableMapping[tuple[int, int], dict], user_a: int, user_b: int) -> dict:
    if user_a == user_b:
        raise ValueError("cannot match self")
    low, high = sorted((user_a, user_b))
    key = (low, high)
    if key not in matches:
        matches[key] = {"user_low_id": low, "user_high_id": high}
    return matches[key]
