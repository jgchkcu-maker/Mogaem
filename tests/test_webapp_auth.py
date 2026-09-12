from __future__ import annotations

import hashlib
import hmac
import json
from urllib.parse import urlencode

import pytest


def signed_init_data(*, bot_token: str, user: dict, auth_date: int, query_id: str = "AAE-test") -> str:
    fields = {
        "auth_date": str(auth_date),
        "query_id": query_id,
        "user": json.dumps(user, separators=(",", ":"), ensure_ascii=False),
    }
    data_check_string = "\n".join(f"{key}={fields[key]}" for key in sorted(fields))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


def test_validate_init_data_accepts_valid_user():
    from mogaem.webapp_auth import validate_init_data

    token = "123456:TEST_TOKEN"
    payload = signed_init_data(
        bot_token=token,
        user={"id": 777000, "first_name": "Nikita", "username": "nikita"},
        auth_date=1_800_000_000,
    )

    actor = validate_init_data(payload, token, max_age_seconds=3600, now=1_800_000_100)
    assert actor.telegram_id == 777000
    assert actor.first_name == "Nikita"
    assert actor.username == "nikita"


def test_validate_init_data_rejects_bad_hash():
    from mogaem.webapp_auth import InvalidInitData, validate_init_data

    token = "123456:TEST_TOKEN"
    payload = signed_init_data(
        bot_token=token,
        user={"id": 777000, "first_name": "Nikita"},
        auth_date=1_800_000_000,
    )
    payload = payload.replace("hash=", "hash=deadbeef")

    with pytest.raises(InvalidInitData):
        validate_init_data(payload, token, max_age_seconds=3600, now=1_800_000_100)


def test_validate_init_data_rejects_expired_payload():
    from mogaem.webapp_auth import ExpiredInitData, validate_init_data

    token = "123456:TEST_TOKEN"
    payload = signed_init_data(
        bot_token=token,
        user={"id": 777000, "first_name": "Nikita"},
        auth_date=1_800_000_000,
    )

    with pytest.raises(ExpiredInitData):
        validate_init_data(payload, token, max_age_seconds=60, now=1_800_000_100)
