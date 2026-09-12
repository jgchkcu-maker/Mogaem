# Mogaem

Telegram-бот знакомств с MOG-оценками.

## Что уже есть в MVP

- обязательная анкета перед поиском;
- имя, возраст 18+, пол, необязательный город, описание и 1–3 фото;
- выбор пола поиска: мужчины / женщины / не важно;
- выдача анкет и оценки `Чад`, `Чад лайт`, `Норми`, `Саб5`, `Саб3`;
- после оценки оценённый пользователь получает анкету того, кто его оценил, и может оценить в ответ;
- после взаимной оценки появляется кнопка запроса на переписку;
- второй пользователь видит обе оценки и принимает или отклоняет запрос;
- после принятия бот открывает контакты обоим;
- уже оценённые анкеты повторно не показываются.

## Локальный запуск

Нужен Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e '.[dev]'
cp .env.example .env
python -m mogaem.bot
```

Для локального теста можно использовать:

```env
DATABASE_URL=sqlite+aiosqlite:///mogaem.db
```

Для реальных пользователей используй PostgreSQL. Временный GitHub Actions runner умеет работать и без него через SQLite + Actions cache, но cache не является полноценной гарантией сохранности пользовательской базы.

## GitHub Secrets

В репозитории открой **Settings → Secrets and variables → Actions → New repository secret**.

Обязательно добавь:

- `BOT_TOKEN` — токен от BotFather.

Опционально добавь:

- `DATABASE_URL` — строка подключения PostgreSQL, например от Neon/Supabase/Railway Postgres. Если её нет, временный GitHub Actions runner использует SQLite и переносит `mogaem.db` между запусками через Actions cache. Для реальных пользователей PostgreSQL надёжнее.

Токен в код, README, issue или commit не добавляй.

## Временный запуск через GitHub Actions

Workflow `Run Mogaem bot` можно запустить вручную через **Actions → Run Mogaem bot → Run workflow**. Также он перезапускается по расписанию. Один запуск работает чуть меньше пяти часов, затем база SQLite сохраняется в Actions cache, и следующий запуск восстанавливает её. Это временная схема: GitHub-hosted Actions предназначены прежде всего для CI/CD, поэтому для постоянной работы потом лучше перенести тот же код на VPS/Railway/Render-подобный сервис и PostgreSQL.

## Тесты

```bash
pytest -q
python -m compileall mogaem
```
