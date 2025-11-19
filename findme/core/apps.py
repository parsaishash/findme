from __future__ import annotations

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self) -> None:  # pragma: no cover - import signals at app load
        try:
            from . import signals  # noqa: F401
        except Exception:
            # Avoid crashing app startup if migrations are pending
            pass
