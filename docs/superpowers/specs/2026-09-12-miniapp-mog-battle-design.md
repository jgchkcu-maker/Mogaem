# Mogaem Mini App + MOG Battle Design

## Goal

Turn the existing Telegram dating/MOG bot into a testable Telegram Mini App while preserving the current bot flows. The Mini App must add pairwise MOG Battle with Elo, leaderboard, profile stats, the existing 1–10 rating feed, and a lightweight matches view. The first deployment target is GitHub Actions with an HTTPS quick tunnel and SQLite; the application architecture must remain portable to a VPS + PostgreSQL later.

## Product surfaces

The Mini App has five bottom-navigation screens:

1. **Battle** — two same-gender active profiles are shown side by side. The voter taps the person who MOGs the other. The server applies Elo and returns the next pair.
2. **Rate** — the existing single-profile 1–10 MOG scale. A user can rate each target once.
3. **Leaderboard** — active profiles ordered by Battle Elo with battle count, record, calibration state, percentile/rank when available, and gender filters.
4. **Matches** — accepted matches from the existing dating flow, with Telegram contact links where available. Pending request handling remains available in the bot during this test iteration.
5. **Profile** — own profile, MOG average, Elo, wins/losses, battle count and calibration state.

The existing Telegram bot continues to own profile creation/editing, chat-request notifications and fallback browsing. The bot menu receives an `Open Mogaem` Web App button pointing at the current tunnel URL.

## Telegram authentication

The browser sends raw `Telegram.WebApp.initData` in `Authorization: tma <initData>`. The backend must validate it using Telegram's Web App HMAC algorithm, compare hashes with `hmac.compare_digest`, require a parseable `user` object, and reject stale `auth_date` values. No endpoint may trust `initDataUnsafe` or a client-supplied Telegram user id.

For automated tests only, application construction may inject an authenticated actor directly; production routes use validated initData.

## Battle model

### Battle rating

Each profile has a lazily-created Battle rating:

- initial Elo: `1000`
- `battles`: 0
- `wins`: 0
- `losses`: 0

K factor is per participant and based on their pre-battle count:

- battles < 10: K = 48
- battles < 50: K = 32
- otherwise K = 20

Expected score:

`E(A) = 1 / (1 + 10 ** ((R(B) - R(A)) / 400))`

The winner gets score 1 and loser score 0. Each side is rounded to the nearest integer after applying that participant's K factor. Elo never drops below 100.

### Battle issue and vote

A `Battle` record is created before the pair is sent to the browser. It contains an opaque random id, voter, left/right participants, sorted pair ids, timestamps and nullable result/Elo snapshots. The client submits only the battle id and selected winner id. The backend resolves both participants from the stored battle. Repeating the same completed vote is idempotent; trying to change its winner is rejected.

A voter never receives themselves, inactive profiles or profiles without photos. Battle participants must have the same gender. The same voter does not receive the same unordered pair twice. Pair selection prefers the smallest Elo distance among available unseen pairs, with randomization among equal-quality candidates.

## Calibration and leaderboard

A profile is calibrating until it has 10 completed battles. Calibrating users still appear in the test leaderboard but are visibly marked and do not receive a stable public rank/percentile. Calibrated profiles receive rank ordered by Elo descending, then battle count descending.

## Existing 1–10 ratings

The current `ratings` table remains the source of MOG average. Mini App rating endpoints call the existing service rules, preserving one rating per ordered pair and the 1–10 labels.

## Photos

Existing photos remain Telegram `file_id` values. The Mini App never sees the bot token. An authenticated backend endpoint resolves the Telegram file via Bot API and streams the bytes to the browser. The first photo is sufficient for Battle/leaderboard cards in this test version.

## Backend/API

FastAPI is added beside aiogram and uses the same SQLAlchemy models/database.

Required endpoints:

- `GET /health`
- `GET /api/me`
- `GET /api/battle/next`
- `POST /api/battle/{battle_id}/vote`
- `GET /api/leaderboard?gender=any|male|female`
- `GET /api/rate/next`
- `POST /api/rate/{target_id}` with `{score: 1..10}`
- `GET /api/matches`
- `GET /api/profiles/{user_id}/photo/{position}`

API errors return JSON with an actionable detail and appropriate 4xx status.

## Frontend

React + TypeScript + Vite. It uses Telegram theme CSS variables where available, calls `Telegram.WebApp.ready()` and `expand()`, enables haptic feedback on votes, and provides responsive mobile-first cards. All API JSON/blob requests attach the validated initData Authorization header.

The frontend displays useful empty states when there are too few profiles, no rating candidates or no matches.

## GitHub Actions test runtime

The production-test workflow:

1. restores best-effort SQLite cache;
2. installs Python dependencies;
3. builds `webapp/dist`;
4. starts FastAPI locally on port 8000;
5. downloads and starts Cloudflare `cloudflared` Quick Tunnel;
6. parses the generated `https://*.trycloudflare.com` URL;
7. configures the bot's Web App menu button to that URL;
8. starts aiogram polling;
9. runs for a bounded period below GitHub's job limit;
10. exits normally so cache post-processing has a chance to save the DB.

This runtime is explicitly test-only. The application itself must depend only on `DATABASE_URL` and normal environment variables so migration to a VPS/PostgreSQL requires deployment changes, not domain rewrites.

## Verification

Completion requires:

- existing tests remain green;
- Elo unit tests cover equal ratings, upset outcomes and K-factor tiers;
- integration tests cover battle creation, vote, duplicate/idempotent vote, exclusion of self/repeated pairs, and leaderboard stats;
- Telegram initData tests cover valid, invalid and expired data;
- Python compilation succeeds;
- Vite production build succeeds in CI;
- merged `main` workflow reaches a healthy FastAPI endpoint, discovers a public tunnel URL, configures the Web App button and reaches running bot polling.
