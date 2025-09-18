"""ASGI config for fileserver project."""
from __future__ import annotations

import os

from django.core.asgi import get_asgi_application

from fileserver.env import load_env

load_env()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fileserver.settings")

application = get_asgi_application()
