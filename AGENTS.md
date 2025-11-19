# Repository Guidelines

## Project Structure & Module Organization
- `findme/` is the Django root with `manage.py`, `.env.example`, and SQLite `db.sqlite3`.
- `findme/findme/` stores global settings, URLs, and `celery.py`; change middleware, env toggles, or worker config here.
- Feature apps live in `core/` (access and tokens), `browser/` (HTMX UI + Celery jobs), and `users/` (auth). Templates/static files sit beside each app, shared layouts stay in `findme/templates/`, and tests are in `findme/tests/`.

## Build, Test, and Development Commands
- `cd findme && cp .env.example .env` before installing deps; fill `DJANGO_SECRET_KEY` and `FILE_SERVER_ROOT`.
- `python manage.py migrate && python manage.py createsuperuser` keeps the local DB current; rerun after editing `core/migrations`.
- `python manage.py runserver 0.0.0.0:8000` drives the UI; run `celery -A findme worker -l info` (plus `celery -A findme beat -l info` when scheduled expirations run).
- `python manage.py collectstatic && python manage.py check --deploy` cover the release checklist before tagging or deploying.

## Coding Style & Naming Conventions
- Target PEP 8 with four-space indents, snake_case modules, PascalCase classes, and type hints as used in `core/models.py`.
- Keep views skinny by moving shared logic into helpers such as `browser/utils.py` so Celery tasks, forms, and HTTP endpoints reuse the same functions.
- Name templates by feature (e.g., `browser/templates/browser/_file_row.html`), prefix app assets under `static/` (like `browser/file-list.js`), and reference them via `{% static %}`.

## Testing Guidelines
- Place Django `TestCase` suites under `findme/tests/test_*.py`, using `tempfile.TemporaryDirectory()` to isolate filesystem writes just like `findmeTestCase`.
- Run `python manage.py test` before committing; narrow loops with `python manage.py test tests.test_findme.findmeTestCase`.
- When touching share links, CLI tokens, HTMX uploads, or Celery downloads, assert permissions, expiry, and rendered fragments.

## Commit & Pull Request Guidelines
- Follow the existing `verb: summary` commits (`add: download jobs`, `fix: hx fragment`) and keep them focused on a single change.
- Separate migrations, template tweaks, and backend logic so reviewers can bisect; document any data migrations inline.
- PRs must state problem, solution, manual verification commands, linked issues (e.g., `Fixes #123`), and attach screenshots or GIFs for UI changes while flagging environment or worker impacts.

## Security & Configuration Notes
- Never commit populated `.env`, `db.sqlite3`, or customer files inside `data/`; use sanitized fixtures under `tests/`.
- Point `FILE_SERVER_ROOT` to a disposable directory in development/tests before writing uploads.
- Production requires `DJANGO_DEBUG=0`, proper `DJANGO_ALLOWED_HOSTS`, HTTPS flags (`DJANGO_SECURE_SSL_REDIRECT`, HSTS), and Celery workers that load the same `.env` so token expiry stays in sync.
