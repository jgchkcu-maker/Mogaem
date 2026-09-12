# Mogaem Mini App + MOG Battle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a working Telegram Mini App test environment that adds MOG Battle/Elo, leaderboard and web access to the existing rating/profile system while preserving the current bot.

**Architecture:** Keep one Python domain/database layer shared by aiogram and FastAPI. Add battle models/services and authenticated API routes, then a React/Vite client served by FastAPI. GitHub Actions builds both surfaces, exposes FastAPI through a Cloudflare Quick Tunnel, configures the bot menu button and runs polling for a bounded test session.

**Tech Stack:** Python 3.12, aiogram 3, FastAPI, SQLAlchemy async, SQLite/PostgreSQL, React 19, TypeScript, Vite, GitHub Actions, cloudflared.

**Spec:** `docs/superpowers/specs/2026-09-12-miniapp-mog-battle-design.md`

## Global Constraints

- Preserve all existing bot/profile/rating/chat-request behavior.
- Production API authentication must use Telegram Web App `initData` HMAC validation.
- Initial Battle Elo is exactly 1000; K tiers are 48 (<10), 32 (<50), 20 (50+); Elo floor is 100.
- Battle pairs are same-gender, exclude voter/inactive/no-photo profiles, and do not repeat for the same voter.
- The browser never receives `BOT_TOKEN` or a Telegram file URL containing the token.
- The Actions runtime is test infrastructure only; domain/API code must remain portable to VPS + PostgreSQL.
- Every backend behavior is implemented test-first; full pytest, compile and frontend build must pass before merge.

---

### Task 1: Battle domain math and persistence

**Files:**
- Create: `mogaem/battle.py`
- Modify: `mogaem/models.py`
- Modify: `mogaem/services.py`
- Test: `tests/test_battle.py`

**Interfaces:**
- Produces `expected_score(rating_a: int, rating_b: int) -> float`, `k_factor(battles: int) -> int`, `updated_elo(rating: int, opponent: int, score: float, battles: int) -> int`.
- Produces SQLAlchemy models `BattleRating` and `Battle`.
- Produces service methods `battle_rating`, `next_battle`, `resolve_battle`, `battle_stats`, `leaderboard`.

- [ ] **Step 1: Write failing Elo tests** for equal ratings, upset result, K-factor boundaries and Elo floor.
- [ ] **Step 2: Run `pytest tests/test_battle.py -q`** and verify imports/behavior fail before implementation.
- [ ] **Step 3: Implement pure Elo helpers** in `mogaem/battle.py` exactly from the spec.
- [ ] **Step 4: Add `BattleRating` and `Battle` models** without changing existing table schemas.
- [ ] **Step 5: Write failing async service tests** creating three profiles and asserting pair eligibility, no self, same gender, one vote mutation, idempotency and unseen-pair behavior.
- [ ] **Step 6: Implement the minimum battle service methods** and transactional stats updates.
- [ ] **Step 7: Run `pytest tests/test_battle.py -q`** until all Battle tests pass.

### Task 2: Telegram Mini App authentication

**Files:**
- Create: `mogaem/webapp_auth.py`
- Modify: `mogaem/config.py`
- Test: `tests/test_webapp_auth.py`

**Interfaces:**
- Produces `TelegramWebAppUser` dataclass and `validate_init_data(init_data: str, bot_token: str, max_age_seconds: int, now: int | None = None) -> TelegramWebAppUser`.
- Adds setting `webapp_auth_max_age_seconds` defaulting to 86400.

- [ ] **Step 1: Write deterministic tests** that construct a correctly signed initData payload with user JSON/auth_date and test valid, bad hash and expired cases.
- [ ] **Step 2: Run `pytest tests/test_webapp_auth.py -q`** and verify RED.
- [ ] **Step 3: Implement parser/HMAC validation** using sorted query fields and `hmac.compare_digest`.
- [ ] **Step 4: Run auth tests** and verify GREEN.

### Task 3: FastAPI Mini App API

**Files:**
- Create: `mogaem/api.py`
- Modify: `pyproject.toml`
- Modify: `mogaem/services.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Produces `create_app(settings: Settings, session_factory=None, actor_override=None) -> FastAPI` and module `app` for uvicorn.
- API endpoints match the design spec.

- [ ] **Step 1: Add FastAPI/uvicorn runtime dependencies** while keeping existing package constraints.
- [ ] **Step 2: Write failing API integration tests** with in-memory SQLite and injected actor for `/health`, `/api/me`, Battle issue/vote, leaderboard, rate next/rate and matches.
- [ ] **Step 3: Implement app lifecycle/database dependency** and authenticated actor dependency.
- [ ] **Step 4: Implement profile serialization and Battle/rating routes** using service methods rather than duplicating business rules.
- [ ] **Step 5: Implement authenticated photo proxy** using Telegram `getFile` + server-side download.
- [ ] **Step 6: Implement accepted matches serialization** in service/API.
- [ ] **Step 7: Run `pytest tests/test_api.py -q`** and fix until GREEN.

### Task 4: React/Vite Telegram Mini App

**Files:**
- Create: `webapp/package.json`
- Create: `webapp/tsconfig.json`
- Create: `webapp/vite.config.ts`
- Create: `webapp/index.html`
- Create: `webapp/src/main.tsx`
- Create: `webapp/src/api.ts`
- Create: `webapp/src/types.ts`
- Create: `webapp/src/App.tsx`
- Create: `webapp/src/styles.css`

**Interfaces:**
- Browser API client attaches `Authorization: tma ${Telegram.WebApp.initData}` to JSON/blob requests.
- Bottom tabs: Battle, Rate, Leaderboard, Matches, Profile.

- [ ] **Step 1: Create Vite/React TypeScript scaffold** with no nonessential UI dependencies.
- [ ] **Step 2: Implement Telegram bootstrap** (`ready`, `expand`, theme variables, haptics) and typed API client.
- [ ] **Step 3: Implement Battle screen** with two image cards, loading/empty/error states and vote animation/state refresh.
- [ ] **Step 4: Implement Rate screen** with single card and 1–10 selector using current MOG names.
- [ ] **Step 5: Implement Leaderboard, Matches and Profile screens** with calibration/status data.
- [ ] **Step 6: Implement mobile-first visual system** using Telegram theme variables, safe areas, glass cards and compact bottom navigation.
- [ ] **Step 7: Run `npm install && npm run build`** in CI and require zero TypeScript/build errors.

### Task 5: Serve frontend and configure bot Web App entry

**Files:**
- Modify: `mogaem/api.py`
- Create: `mogaem/configure_webapp.py`
- Modify: `mogaem/bot.py`
- Test: `tests/test_runtime_helpers.py`

**Interfaces:**
- FastAPI serves `webapp/dist/assets/*` and SPA `index.html` for non-API routes.
- `python -m mogaem.configure_webapp <https-url>` sets the bot default menu button to a Telegram Web App button.

- [ ] **Step 1: Add tests for URL validation/menu-button construction and static fallback behavior.**
- [ ] **Step 2: Implement static serving** that does not shadow `/api/*` or `/health`.
- [ ] **Step 3: Implement `configure_webapp.py`** using aiogram `MenuButtonWebApp` + `WebAppInfo`, refusing non-HTTPS URLs.
- [ ] **Step 4: Add `/start`/menu discoverability** without removing existing inline/reply controls.
- [ ] **Step 5: Run targeted runtime helper tests** and compile.

### Task 6: GitHub Actions CI and test deployment

**Files:**
- Modify: `.github/workflows/ci.yml`
- Replace: `.github/workflows/bot.yml`
- Modify: `.gitignore`
- Modify: `.env.example`
- Modify: `README.md`

**Interfaces:**
- CI builds Python + frontend.
- Runtime workflow starts API, cloudflared tunnel, updates Telegram menu URL and starts bot polling.

- [ ] **Step 1: Extend CI** with Node 22 setup, `npm install`, `npm run build`, while retaining pytest/compile.
- [ ] **Step 2: Change runtime workflow** to install/build frontend, download cloudflared, restore SQLite cache, launch uvicorn, wait for `/health`, launch tunnel, parse URL, run `configure_webapp`, then poll the bot under a bounded timeout.
- [ ] **Step 3: Make normal shutdown precede job timeout** so cache post-step can execute; retain a single concurrency group to avoid multiple bot pollers.
- [ ] **Step 4: Update README/env example** with test-runtime limitations and future VPS/PostgreSQL migration variables.
- [ ] **Step 5: Push and inspect GitHub Actions**; fix Python or frontend failures until CI is green.

### Task 7: Merge and production-test verification

**Files:** no new functional files unless verification reveals a defect.

- [ ] **Step 1: Review branch diff** for accidental secrets, duplicate business logic and unrelated edits.
- [ ] **Step 2: Open PR** with test evidence and known test-runtime limitations.
- [ ] **Step 3: Merge only after branch CI passes.**
- [ ] **Step 4: Verify `main` CI passes.**
- [ ] **Step 5: Verify runtime job reaches FastAPI health, discovers a `trycloudflare.com` URL, successfully configures the Telegram Web App menu, and reaches active aiogram polling.**
- [ ] **Step 6: Report the actual public Mini App URL and workflow run, plus the single remaining infrastructure caveat: GitHub Actions/SQLite is ephemeral test hosting.**
