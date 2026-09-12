from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl


class InvalidInitData(ValueError):
    pass


class ExpiredInitData(InvalidInitData):
    pass


@dataclass(frozen=True, slots=True)
class TelegramWebAppUser:
    telegram_id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    is_premium: bool = False


def validate_init_data(
    init_data: str,
    bot_token: str,
    *,
    max_age_seconds: int = 86400,
    now: int | None = None,
) -> TelegramWebAppUser:
    if not init_data:
        raise InvalidInitData("empty initData")
    if not bot_token:
        raise InvalidInitData("bot token is not configured")

    fields = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = fields.pop("hash", None)
    if not received_hash:
        raise InvalidInitData("hash is missing")

    data_check_string = "\n".join(f"{key}={fields[key]}" for key in sorted(fields))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(received_hash, expected_hash):
        raise InvalidInitData("invalid initData signature")

    try:
        auth_date = int(fields["auth_date"])
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidInitData("auth_date is missing or invalid") from exc

    current_time = int(time.time()) if now is None else int(now)
    if auth_date > current_time + 30:
        raise InvalidInitData("auth_date is in the future")
    if max_age_seconds >= 0 and current_time - auth_date > max_age_seconds:
        raise ExpiredInitData("initData has expired")

    try:
        raw_user = json.loads(fields["user"])
        telegram_id = int(raw_user["id"])
        first_name = str(raw_user["first_name"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise InvalidInitData("user payload is missing or invalid") from exc

    return TelegramWebAppUser(
        telegram_id=telegram_id,
        first_name=first_name,
        last_name=raw_user.get("last_name"),
        username=raw_user.get("username"),
        language_code=raw_user.get("language_code"),
        is_premium=bool(raw_user.get("is_premium", False)),
    )
