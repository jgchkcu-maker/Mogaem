# Mogaem

Telegram MOG/dating проект: бот + Telegram Mini App.

## Что есть

### Telegram-бот

- обязательная анкета перед поиском;
- имя, возраст 18+, пол, необязательный город, описание и 1–3 фото;
- выбор пола поиска: мужчины / женщины / не важно;
- MOG-оценка внешности по шкале 1–10 (`Гигачад` → `Блэкпилл`);
- оценённый пользователь получает анкету автора оценки и может оценить в ответ;
- после взаимных оценок можно отправить запрос на переписку;
- после принятия запроса бот открывает контакты обоим;
- анкета может быть отключена и восстановлена без потери фото/рейтинга.

### Telegram Mini App

Новая Mini App использует ту же базу и содержит пять вкладок:

- `⚔️ Battle` — две анкеты одного пола, выбор кто MOG'ает, моментальный перерасчёт Elo;
- `🔥 Оценка` — текущая одиночная MOG-оценка 1–10;
- `🏆 Рейтинг` — leaderboard по Battle Elo с фильтром пола;
- `💘 Матчи` — принятые знакомства и переход к Telegram-контакту;
- `👤 Профиль` — MOG Score, Battle Elo, wins/losses и калибровка.

MOG Score и Battle Elo — разные показатели. Средняя оценка 1–10 хранится в `ratings`; сравнительный рейтинг Battle хранится отдельно.

## Battle Elo

Начальный Elo: `1000`.

K-factor:

- первые 10 баттлов: `48`;
- 10–49 баттлов: `32`;
- 50+ баттлов: `20`.

До 10 завершённых баттлов профиль находится в калибровке. Один голосующий не получает одну и ту же неупорядоченную пару дважды. Себя, отключённые анкеты и анкеты без фото Battle не показывает.

## Telegram Mini App auth

Frontend отправляет сырой `Telegram.WebApp.initData` в `Authorization: tma ...`. Backend проверяет Telegram HMAC-подпись и `auth_date`; client-side `initDataUnsafe` не используется как источник доверия.

Фото остаются Telegram `file_id`: браузер получает их только через авторизованный backend proxy, `BOT_TOKEN` во frontend не передаётся.

## Локальный backend

Нужен Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e '.[dev]'
cp .env.example .env
python -m uvicorn mogaem.api:app --reload
```

В другом терминале:

```bash
python -m mogaem.bot
```

Для локального теста:

```env
DATABASE_URL=sqlite+aiosqlite:///mogaem.db
```

Для постоянного сервера используй PostgreSQL.

## Локальный Mini App frontend

Нужен Node.js 22+.

```bash
cd webapp
npm install
npm run dev
```

Production build:

```bash
npm run build
```

FastAPI автоматически раздаёт `webapp/dist`, если production build существует.

## GitHub Secrets

**Settings → Secrets and variables → Actions**:

- `BOT_TOKEN` — обязательно;
- `DATABASE_URL` — опционально. Без него тестовый runner использует SQLite + Actions cache.

Никогда не добавляй токен в git/README/issues.

## Тестовый Mini App через GitHub Actions

Workflow **Run Mogaem test runtime** предназначен только для проверки продукта до переезда на собственный сервер.

Каждый запуск:

1. восстанавливает `mogaem.db` из best-effort Actions cache;
2. собирает React/Vite Mini App;
3. запускает FastAPI на localhost;
4. создаёт HTTPS Cloudflare Quick Tunnel (`*.trycloudflare.com`);
5. проверяет публичный `/health`;
6. автоматически ставит этот URL в Telegram menu button `⚔️ Mogaem`;
7. запускает aiogram polling;
8. завершается до лимита job, чтобы cache успел сохраниться;
9. запускается снова каждый час.

При push в `main` текущий тестовый runtime отменяется и запускается новый. Поэтому SQLite/cache **не является гарантированным постоянным хранилищем** — при отмене job последние изменения могут потеряться. Это допустимо только для теста.

Для production переносится тот же код: FastAPI + bot на VPS/Docker/systemd, `DATABASE_URL` переключается на PostgreSQL, а временный tunnel заменяется постоянным HTTPS-доменом. Battle/API/frontend переписывать для этого не нужно.

## Проверки

```bash
pytest -q
python -m compileall -q mogaem
cd webapp && npm install && npm run build
```

CI выполняет все три проверки на `main` и `feat/**`.
