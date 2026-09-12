# Mogaem MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a runnable Telegram MOG/dating bot implementing mandatory profiles, gender-filtered browsing, MOG ratings, reciprocal rating, chat requests, and accept/decline matches.

**Architecture:** aiogram handlers are thin adapters over SQLAlchemy-backed domain services. Profile/rating/request/match rules live in services so they can be tested without Telegram. GitHub Actions runs CI and temporarily runs long polling using repository secrets.

**Tech Stack:** Python 3.12, aiogram 3, SQLAlchemy 2 async, aiosqlite for tests/local use, asyncpg for PostgreSQL, pytest/pytest-asyncio.

**Spec:** `docs/superpowers/specs/2026-09-12-mogaem-mvp-design.md`

## Global Constraints
- Profiles are 18+ only.
- City is optional.
- Search gender is `male`, `female`, or `any`.
- Rating labels are `Chad`, `Chad-lite`, `Normie`, `Sub5`, `Sub3`.
- A chat request requires reciprocal ratings.
- Secrets never live in source code.

---

### Task 1: Domain model and database
**Files:** `pyproject.toml`, `mogaem/config.py`, `mogaem/db.py`, `mogaem/models.py`, `tests/test_domain.py`

- [ ] Write failing tests for profile validation, candidate filtering, unique ratings, reciprocal-rating requirement, request resolution, and idempotent matches.
- [ ] Run `pytest -q` and confirm failures are caused by missing implementation.
- [ ] Implement SQLAlchemy models, async DB setup, and domain service functions minimally to satisfy tests.
- [ ] Run `pytest -q` until green.

### Task 2: Telegram profile onboarding and browsing
**Files:** `mogaem/states.py`, `mogaem/keyboards.py`, `mogaem/render.py`, `mogaem/handlers/profile.py`, `mogaem/handlers/browse.py`, `mogaem/bot.py`

- [ ] Add handler-focused unit tests for pure parsing/render helpers first.
- [ ] Implement `/start`, mandatory profile FSM, photo collection, optional city, main menu, browsing and rating callbacks.
- [ ] Ensure rating a profile triggers a notification to the rated user with the rater's profile and reciprocal-rating controls.
- [ ] Run full tests.

### Task 3: Chat request lifecycle
**Files:** `mogaem/handlers/requests.py`, `mogaem/keyboards.py`, `mogaem/render.py`

- [ ] Add failing service/format tests for request creation and confirmation card content.
- [ ] Implement `Send chat request`, recipient confirmation with both ratings, accept/decline, and contact delivery.
- [ ] Run full tests.

### Task 4: Runtime, documentation, and GitHub Actions
**Files:** `.env.example`, `.gitignore`, `README.md`, `.github/workflows/ci.yml`, `.github/workflows/bot.yml`

- [ ] Add config validation tests where applicable.
- [ ] Document local setup and required GitHub Secrets.
- [ ] Add CI workflow and temporary long-polling workflow.
- [ ] Run `python -m compileall mogaem` and `pytest -q`.

### Task 5: Integration review
- [ ] Verify imports and syntax.
- [ ] Verify no token/database credentials are committed.
- [ ] Verify GitHub diff matches the spec.
- [ ] Open a pull request from `feat/mog-mvp` to `main`.
