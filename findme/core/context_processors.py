"""Custom context processors for global template context."""
from __future__ import annotations

from django.conf import settings
from django.http import HttpRequest


def app_context(request: HttpRequest) -> dict[str, str]:
    """Provide global template context values."""
    theme = request.session.get("theme", settings.DEFAULT_THEME)
    return {
        "app_version": "v1.0.0",
        "app_name": "FindMe",
        "theme": theme,
    }
