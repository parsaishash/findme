"""ASGI config for the FindMe project."""
from __future__ import annotations

import os

from django.core.asgi import get_asgi_application

from findme.env import load_env

load_env()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "findme.settings")

application = get_asgi_application()
