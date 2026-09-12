import pytest

from mogaem.domain import (
    DuplicateRatingError,
    ReciprocalRatingRequired,
    create_chat_request,
    create_or_get_match,
    create_rating,
    eligible_candidate,
    validate_profile,
)


def test_profile_requires_adult_age():
    with pytest.raises(ValueError):
        validate_profile(name="N", age=17, gender="male", search_gender="any", bio="x")


def test_optional_city_is_valid():
    result = validate_profile(name="Nikita", age=18, gender="male", search_gender="female", bio="hi", city=None)
    assert result["city"] is None


def test_gender_filter_any_and_specific():
    assert eligible_candidate(viewer_id=1, candidate_id=2, search_gender="any", candidate_gender="female", already_rated=False)
    assert eligible_candidate(viewer_id=1, candidate_id=2, search_gender="female", candidate_gender="female", already_rated=False)
    assert not eligible_candidate(viewer_id=1, candidate_id=2, search_gender="male", candidate_gender="female", already_rated=False)


def test_candidate_excludes_self_and_already_rated():
    assert not eligible_candidate(viewer_id=1, candidate_id=1, search_gender="any", candidate_gender="male", already_rated=False)
    assert not eligible_candidate(viewer_id=1, candidate_id=2, search_gender="any", candidate_gender="male", already_rated=True)


def test_duplicate_rating_rejected():
    ratings = {(1, 2): "9"}
    with pytest.raises(DuplicateRatingError):
        create_rating(ratings, rater_id=1, rated_id=2, label="6")


def test_chat_request_needs_reciprocal_ratings():
    ratings = {(1, 2): "9"}
    with pytest.raises(ReciprocalRatingRequired):
        create_chat_request([], ratings, requester_id=2, recipient_id=1)


def test_chat_request_contains_both_ratings():
    ratings = {(1, 2): "9", (2, 1): "8"}
    request = create_chat_request([], ratings, requester_id=2, recipient_id=1)
    assert request["requester_rating"] == "8"
    assert request["recipient_rating"] == "9"
    assert request["status"] == "pending"


def test_match_creation_is_idempotent_and_unordered():
    matches = {}
    first = create_or_get_match(matches, 4, 2)
    second = create_or_get_match(matches, 2, 4)
    assert first is second
    assert first["user_low_id"] == 2
    assert first["user_high_id"] == 4
