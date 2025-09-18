"""Minimal .env loader used for local development and deployment."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_ENV_PATH = BASE_DIR / ".env"


def _parse_line(line: str) -> Tuple[str, str] | None:
    """Parse a line from a .env file into a key/value pair."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if stripped.startswith("export "):
        stripped = stripped[len("export ") :]
    if "=" not in stripped:
        return None
    key, value = stripped.split("=", 1)
    key = key.strip()
    if not key:
        return None
    value = value.strip().strip("\"' ")
    return key, value


def load_env(path: Path | str | None = None, *, override: bool = False) -> None:
    """Load environment variables from a .env file.

    Parameters
    ----------
    path: Path | str | None
        Path to the .env file (defaults to ``BASE_DIR / ".env"``).
    override: bool
        When True, variables from the file override already-defined values.
    """

    env_path = Path(path) if path is not None else DEFAULT_ENV_PATH
    if not env_path.exists() or not env_path.is_file():
        return

    with env_path.open("r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            parsed = _parse_line(raw_line)
            if not parsed:
                continue
            key, value = parsed
            if override:
                os.environ[key] = value
            else:
                os.environ.setdefault(key, value)


__all__ = ["load_env", "DEFAULT_ENV_PATH", "BASE_DIR"]
