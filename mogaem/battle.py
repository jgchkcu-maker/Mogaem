from __future__ import annotations


def expected_score(rating_a: int, rating_b: int) -> float:
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


def k_factor(battles: int) -> int:
    if battles < 10:
        return 48
    if battles < 50:
        return 32
    return 20


def updated_elo(rating: int, opponent: int, score: float, battles: int) -> int:
    expected = expected_score(rating, opponent)
    updated = round(rating + k_factor(battles) * (score - expected))
    return max(100, updated)
