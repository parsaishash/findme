# FindMe

FindMe is a minimal, secure Django file server that supports browsing, uploads, streaming downloads (with optional compression), share links, CLI tokens, and superadmin user management. The UI follows the Apple-like aesthetic defined in the project specification.

## Setup

1. Copy the example environment file and customise it for your machine:

   ```bash
   cp .env.example .env
   ```

   At minimum set a unique `DJANGO_SECRET_KEY` when you plan to deploy beyond localhost.

2. Create a virtual environment and install dependencies (the project uses [uv](https://github.com/astral-sh/uv) for dependency management):

   ```bash
   uv venv
   source .venv/bin/activate
   uv pip sync requirements.txt
   ```

   If you prefer `pip`, run `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.

3. Apply migrations:

   ```bash
   python manage.py migrate
   ```

4. Create an initial superuser:

   ```bash
   python manage.py createsuperuser
   ```

5. Create groups and file access rules via the Django admin or the shell. Example:

   ```bash
   python manage.py shell
   >>> from django.contrib.auth.models import Group
   >>> from core.models import FileAccessRule
   >>> devs = Group.objects.create(name="devs")
   >>> FileAccessRule.objects.create(group=devs, path="projects/dev")
   ```

6. Run the development server:

   ```bash
   python manage.py runserver
   ```

### Docker deployment

The repository ships with a lightweight Dockerfile that installs dependencies via `uv` and a `docker-compose.yml` that keeps the stack small (web app, Celery worker/beat, and Redis). To deploy with Docker:

1. Copy `.env.example` to `.env` and update secrets/paths. When running in containers, set `FILE_SERVER_ROOT=/data` (the compose file already enforces this).
2. Build the images:

   ```bash
   docker compose build
   ```

3. Apply database migrations inside the container and create a superuser:

   ```bash
   docker compose run --rm web python manage.py migrate
   docker compose run --rm web python manage.py createsuperuser
   ```

4. (Optional) Collect static files for production:

   ```bash
   docker compose run --rm web python manage.py collectstatic --noinput
   ```

5. Start the stack:

   ```bash
   docker compose up -d web worker beat redis
   ```

The `data` named volume stores uploaded files, so it persists across container restarts. Celery services share the same image as the web process to keep dependency management simple.

## Production Deployment

1. Copy `.env.example` to `.env` (or create a new file) and set:
   - `DJANGO_ENV=production`
   - `DJANGO_DEBUG=0`
   - `DJANGO_SECRET_KEY` to a long random string
   - `DJANGO_ALLOWED_HOSTS` to the domain(s) you will serve
   - `DJANGO_CSRF_TRUSTED_ORIGINS=https://your-domain`
   - Enable HTTPS hardening with `DJANGO_SECURE_SSL_REDIRECT=1` and a non-zero `DJANGO_SECURE_HSTS_SECONDS`

2. Collect static files and run Django's deployment checks:

   ```bash
   python manage.py collectstatic
   python manage.py check --deploy
   ```

3. Run the application with a WSGI server such as gunicorn or behind a reverse proxy:

   ```bash
   gunicorn findme.wsgi:application --bind 0.0.0.0:8000
   ```

4. Configure your reverse proxy (nginx/Caddy/Apache) to serve `/static/` from `staticfiles/`, `/media/` from `media/`, proxy the remaining requests to gunicorn, and forward `X-Forwarded-Proto`/`X-Forwarded-Host` headers. Enable the matching options in `.env` if required.

## Features

- **Authentication** – All routes (except share links) require login. Superadmins see the user management console.
- **File browser** – Browse files/folders under `FILE_SERVER_ROOT`, trigger downloads, archive downloads, uploads, and share links via the inline actions menu.
- **Uploads** – Upload from the browser or via CLI (`curl -F "files=@report.pdf" http://host/upload/projects/dev/`).
- **Streaming downloads** – Files stream directly; folders can be streamed as `.tar.gz` or `.zip` archives.
- **Share links** – Generate expiring public URLs that do not require authentication.
- **CLI tokens** – Temporary tokens for `curl`/`wget` usage (`?token=...`).
- **User management** – Superadmins can create users, reset passwords, toggle activation, assign groups, and delete accounts without using Django admin.

## Testing

Run the automated test suite:

```bash
python manage.py test
```

The tests cover CLI token generation, share link expiry, access control, and download/upload authorization scenarios.

## Configuration

Environment variables:

| Variable | Description | Default |
| --- | --- | --- |
| `DJANGO_ENV` | Deployment environment label | `development` |
| `DJANGO_SECRET_KEY` | Django secret key | `unsafe-development-secret-key` |
| `DJANGO_DEBUG` | Enable Django debug mode (`1` truthy, `0` falsey) | `1` when `DJANGO_ENV` is `development` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames Django will serve | `127.0.0.1,localhost` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Comma-separated list of fully-qualified origins for CSRF checks | _unset_ |
| `DJANGO_SECURE_SSL_REDIRECT` | Force HTTPS redirects | `1` when `DJANGO_ENV` is not development |
| `DJANGO_SECURE_HSTS_SECONDS` | HTTP Strict-Transport-Security lifetime in seconds | `0` in development, `31536000` otherwise |
| `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS` | Apply HSTS to subdomains | `1` when `DJANGO_SECURE_HSTS_SECONDS > 0` |
| `DJANGO_SECURE_HSTS_PRELOAD` | Opt into browser HSTS preload list | `0` |
| `DJANGO_LOG_LEVEL` | Log level for Django and application logs | `DEBUG` in development, `INFO` otherwise |
| `DJANGO_SESSION_COOKIE_SECURE` | Send session cookies over HTTPS only | `1` when `DJANGO_ENV` is not development |
| `DJANGO_CSRF_COOKIE_SECURE` | Send CSRF cookies over HTTPS only | `1` when `DJANGO_ENV` is not development |
| `DJANGO_SESSION_COOKIE_SAMESITE` | SameSite attribute for session cookies | `Lax` |
| `DJANGO_CSRF_COOKIE_SAMESITE` | SameSite attribute for CSRF cookies | `Lax` |
| `DJANGO_USE_X_FORWARDED_HOST` | Trust `X-Forwarded-Host` from a reverse proxy | `0` |
| `DJANGO_USE_X_FORWARDED_PROTO` | Trust `X-Forwarded-Proto` from a reverse proxy | Mirrors `DJANGO_USE_X_FORWARDED_HOST` |
| `FILE_SERVER_ROOT` | Base directory for file storage | `<project>/data/` |
| `TOKEN_EXPIRY_HOURS` | Default CLI token lifetime | `1` |
| `SHARE_LINK_EXPIRY_HOURS` | Default share link lifetime | `24` |
| `FINDME_DEFAULT_THEME` | Light or dark theme preset (falls back to `FILESERVER_DEFAULT_THEME`) | `light` |
| `TRAEFIK_HOST` | Hostname used in docker labels when Traefik fronts the stack | `files.example.com` |
| `TRAEFIK_ENTRYPOINTS` | Traefik entrypoints for HTTPS routing | `websecure` |
| `TRAEFIK_CERTRESOLVER` | Traefik certificate resolver name | `le` |
| `TRAEFIK_ACME_EMAIL` | Contact email used by Traefik's ACME resolver (only needed when using the bundled Traefik profile) | `admin@example.com` |

### Traefik via docker compose labels

Traefik can either exist outside of this project or run alongside FindMe by enabling the optional compose profile. The `web` service is pre-labeled for Traefik:

- Set `TRAEFIK_HOST`, `TRAEFIK_ENTRYPOINTS`, and `TRAEFIK_CERTRESOLVER` in `.env`.
- When an existing Traefik instance is already running, connect it to the `findme_proxy` network that `docker compose` creates:

  ```bash
  docker network connect findme_proxy <existing-traefik-container>
  docker compose up -d web worker beat redis
  ```

  Traefik immediately picks up the labels and forwards requests to port 8000 inside the `web` container.

- If you want to ship Traefik with FindMe, enable the included profile. This spins up Traefik, terminates TLS, and routes traffic using the same labels:

  ```bash
  docker compose --profile traefik up -d traefik web worker beat redis
  ```

  Replace `TRAEFIK_ACME_EMAIL` with your own email address so Let's Encrypt renewals succeed.

If you are not using Traefik, remove the labels from `docker-compose.yml` and add `ports: ["8000:8000"]` under the `web` service to expose Django directly.

## CLI Examples

```
# Download a file using basic auth
curl -u alice:password http://localhost:8000/download/file/projects/dev/notes.txt

# Download a folder as zip using a token
curl -O "http://localhost:8000/download/folder/projects/dev/?format=zip&token=ABC123"

# Upload via CLI
curl -u alice:password -F "files=@report.pdf" http://localhost:8000/upload/projects/dev/
```

## Light/Dark Mode

Users can toggle light/dark themes from the navbar. The preference is stored in the session.

## Health Check

A simple readiness endpoint is available at `/health/` returning `{"status": "ok"}`.
