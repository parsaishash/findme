"""Django settings for the FindMe project."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict

from findme.env import load_env

load_env()

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    """Read a boolean environment variable."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str | None = None) -> list[str]:
    """Read a comma-separated list from the environment."""
    raw = os.environ.get(name)
    if raw is None:
        raw = default or ""
    return [item.strip() for item in raw.split(",") if item.strip()]


def env_log_level(name: str, default: str) -> str:
    """Return a valid logging level name from the environment."""
    raw = os.environ.get(name, default)
    if not isinstance(raw, str):
        return default.upper()
    level_name = raw.strip().upper()
    if level_name not in logging._nameToLevel:
        return default.upper()
    return level_name


ENVIRONMENT = os.environ.get("DJANGO_ENV", "development").strip().lower() or "development"
DEBUG = env_bool("DJANGO_DEBUG", default=ENVIRONMENT in {"development", "dev", "local"})

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "unsafe-development-secret-key")

if not DEBUG and SECRET_KEY == "unsafe-development-secret-key":
    raise ValueError("DJANGO_SECRET_KEY must be set when DEBUG is False.")

# Root endpoint prefix for URL routing (useful when running behind a reverse proxy)
ROOT_ENDPOINT = os.environ.get("DJANGO_ROOT_ENDPOINT", "/").strip()
if not ROOT_ENDPOINT.startswith("/"):
    ROOT_ENDPOINT = "/" + ROOT_ENDPOINT
if not ROOT_ENDPOINT.endswith("/"):
    ROOT_ENDPOINT = ROOT_ENDPOINT + "/"

# FORCE_SCRIPT_NAME is used when the reverse proxy strips the prefix
# This ensures Django generates URLs with the correct prefix
FORCE_SCRIPT_NAME = os.environ.get("FORCE_SCRIPT_NAME", ROOT_ENDPOINT.rstrip("/") if ROOT_ENDPOINT != "/" else None)

ALLOWED_HOSTS: list[str] = env_list("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost")
CSRF_TRUSTED_ORIGINS: list[str] = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django_celery_beat",
    "core",
    "browser",
    "users",
]

# Celery (Redis broker/backend by default)
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = os.environ.get("TZ", "UTC")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "findme.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.app_context",
            ],
        },
    },
]

WSGI_APPLICATION = "findme.wsgi.application"
ASGI_APPLICATION = "findme.asgi.application"

# Database
DATABASES: Dict[str, Dict[str, Any]] = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static and media URLs
# Note: When FORCE_SCRIPT_NAME is set, Django automatically prepends it to URLs
# So we use relative paths here
STATIC_URL = f"{ROOT_ENDPOINT}static/" if FORCE_SCRIPT_NAME else "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = f"{ROOT_ENDPOINT}media/" if FORCE_SCRIPT_NAME else "/media/"
MEDIA_ROOT = BASE_DIR / "media"

LOGIN_URL = "core:login"
LOGIN_REDIRECT_URL = "browser:root"
LOGOUT_REDIRECT_URL = "core:login"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Security hardening for production
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", default=not DEBUG)
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "0" if DEBUG else "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=SECURE_HSTS_SECONDS > 0
)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", default=False)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", default=not DEBUG)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = os.environ.get("DJANGO_SESSION_COOKIE_SAMESITE", "Lax")
CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", default=not DEBUG)
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = os.environ.get("DJANGO_CSRF_COOKIE_SAMESITE", "Lax")
REFERRER_POLICY = os.environ.get("DJANGO_REFERRER_POLICY", "strict-origin-when-cross-origin")
USE_X_FORWARDED_HOST = env_bool("DJANGO_USE_X_FORWARDED_HOST", default=False)

if env_bool("DJANGO_USE_X_FORWARDED_PROTO", default=USE_X_FORWARDED_HOST):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

X_FRAME_OPTIONS = os.environ.get("DJANGO_X_FRAME_OPTIONS", "DENY")

LOG_LEVEL = env_log_level("DJANGO_LOG_LEVEL", "DEBUG" if DEBUG else "INFO")
LOG_LEVEL = "INFO"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(levelname)s %(asctime)s %(name)s %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        }
    },
}

# File server configuration
FILE_SERVER_ROOT = Path(os.environ.get("FILE_SERVER_ROOT", BASE_DIR / "data")).resolve()
FILE_SERVER_ROOT.mkdir(parents=True, exist_ok=True)

TOKEN_EXPIRY_HOURS = int(os.environ.get("TOKEN_EXPIRY_HOURS", 1))
SHARE_LINK_EXPIRY_HOURS = int(os.environ.get("SHARE_LINK_EXPIRY_HOURS", 24))

# Light/dark theme default
DEFAULT_THEME = os.environ.get("FINDME_DEFAULT_THEME") or os.environ.get("FILESERVER_DEFAULT_THEME", "light")

# Email configuration defaults to console backend in development
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
