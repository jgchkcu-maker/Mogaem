# Mogaem MVP Design

## Goal
Build a Telegram dating/MOG bot where a completed profile is required before browsing, users rate other profiles with MOG labels, the rated person is notified with the rater's profile, and a two-step chat request can be approved or rejected after both sides have rated each other.

## Product flow
1. `/start` requires profile creation before any other product flow.
2. Profile fields: display name, age (18+), gender (`male`/`female`), optional city, short bio, 1-3 photos, search gender (`male`/`female`/`any`).
3. Browse shows one eligible profile at a time, filtered by search gender. City is informational in MVP, not a hard filter.
4. Rating scale is configurable. MVP values, best to worst: `Chad`, `Chad-lite`, `Normie`, `Sub5`, `Sub3`.
5. When A rates B, B receives A's profile and the rating A gave B.
6. B can rate A from that notification. A chat request can only be sent after B has rated A, so the confirmation card can show both ratings.
7. If B taps `Send chat request`, A receives both profile cards/identities and both ratings, then chooses `Accept` or `Decline`.
8. On accept, a match is created once and both users receive the other user's Telegram contact/username when available. If a username is absent, the bot provides a `tg://user?id=...` link.
9. On decline, the request is closed and cannot be accepted later.
10. Profiles already rated by the browsing user are not shown again in normal browsing.

## Telegram UX
- Pure Telegram bot for MVP, using inline keyboards.
- Main menu: `Browse`, `My profile`, `Search gender`.
- Profile cards use first photo with caption; additional photos may be sent as a media group during profile preview.
- Callback data is compact and validated server-side.

## Architecture
- Python 3.12.
- aiogram 3 for Telegram polling and FSM.
- SQLAlchemy 2 async models/repositories.
- PostgreSQL in real runs via `DATABASE_URL`; SQLite supported locally/tests.
- Telegram `file_id` values are stored instead of downloading images.
- Domain services own matching/rating/request rules so handlers stay thin and testable.

## Data model
### users
- `id` internal integer PK
- `telegram_id` unique bigint
- `username` nullable
- `created_at`

### profiles
- `user_id` unique FK users
- `name`
- `age`
- `gender` enum/string
- `search_gender` enum/string
- `city` nullable
- `bio`
- `is_active`

### photos
- `id`
- `user_id`
- `file_id`
- `position`

### ratings
- `id`
- `rater_id`
- `rated_id`
- `label`
- unique (`rater_id`, `rated_id`)
- `created_at`

### chat_requests
- `id`
- `requester_id`
- `recipient_id`
- `status` (`pending`, `accepted`, `declined`)
- unique pending request per pair/direction enforced in service logic
- `created_at`, `resolved_at`

### matches
- `id`
- `user_low_id`
- `user_high_id`
- unique unordered pair
- `created_at`

## Eligibility rules
A candidate must:
- have an active complete profile,
- not be the browsing user,
- match the browsing user's `search_gender` unless it is `any`,
- not already have been rated by the browsing user.

## Safety / integrity
- Profiles are 18+ only in MVP.
- Server-side validation for callback ownership and transitions.
- Duplicate ratings are rejected.
- Duplicate chat requests are rejected.
- Match creation is idempotent.
- Bot token and database URL are environment secrets only.

## Deployment
- GitHub Actions temporarily runs the bot with long polling.
- Workflow uses repository secrets `BOT_TOKEN` and `DATABASE_URL`.
- A separate CI workflow runs tests on pushes and pull requests.
- GitHub Actions is acknowledged as a temporary runtime; the app can later move unchanged to Railway/VPS/Render-style hosting.

## Testing
Automated tests cover:
- profile completeness and 18+ validation,
- gender filtering,
- exclusion of already-rated profiles,
- rating creation/duplicate rejection,
- requirement for reciprocal rating before chat request,
- chat request accept/decline rules,
- idempotent match creation.
