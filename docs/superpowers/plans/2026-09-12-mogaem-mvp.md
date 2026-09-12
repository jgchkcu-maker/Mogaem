# Mogaem MVP Implementation Plan

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

## Completed
- [x] Domain model and database
- [x] Mandatory profile onboarding
- [x] Gender-filtered browsing
- [x] MOG ratings and reciprocal notifications
- [x] Chat request accept/decline lifecycle
- [x] Contact delivery on accepted match
- [x] Token-only temporary GitHub Actions runner with SQLite cache
- [x] Optional PostgreSQL/Neon support
- [x] CI, runtime import test, DB integration test and compile check
- [x] Pull request opened against `main`

## Verification
GitHub Actions on Python 3.12 successfully installed aiogram, SQLAlchemy, aiosqlite and asyncpg. The full suite reported `16 passed`; `python -m compileall -q mogaem` passed. The integration test creates two users/profiles in SQLite, filters candidates, stores reciprocal ratings, creates a chat request and resolves an accepted match.
