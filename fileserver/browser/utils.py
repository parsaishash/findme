"""Utility helpers for file path validation, listing, and streaming."""
from __future__ import annotations

import mimetypes
import os
import queue
import threading
from dataclasses import dataclass
import datetime
from pathlib import Path, PurePosixPath
from typing import Iterable, Iterator

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import FileResponse, Http404, StreamingHttpResponse

from core.models import CLIToken, FileAccessRule

CHUNK_SIZE = 1024 * 256  # 256 KB


@dataclass(frozen=True)
class Entry:
    """Representation of a file system entry for template consumption."""

    name: str
    path: str
    is_dir: bool
    size: int
    modified: float

    @property
    def extension(self) -> str:
        return os.path.splitext(self.name)[1].lower()


class QueueWriter:
    """File-like object that pushes write payloads into a queue."""

    def __init__(self) -> None:
        self._queue: queue.SimpleQueue[bytes | None] = queue.SimpleQueue()

    def write(self, data: bytes) -> None:
        if data:
            self._queue.put(data)

    def close(self) -> None:
        self._queue.put(None)

    def __iter__(self) -> Iterator[bytes]:
        while True:
            chunk = self._queue.get()
            if chunk is None:
                break
            yield chunk


def normalize_path(raw_path: str) -> str:
    """Sanitize incoming path ensuring no traversal and consistent format."""
    posix_path = PurePosixPath("/" + raw_path.strip("/"))
    safe_parts = [part for part in posix_path.parts if part not in {"..", "."}]
    normalized = str(PurePosixPath(*safe_parts)).lstrip("/")
    return normalized


def resolve_target_path(raw_path: str) -> Path:
    """Resolve a raw relative path against the FILE_SERVER_ROOT securely."""
    normalized = normalize_path(raw_path)
    root = Path(settings.FILE_SERVER_ROOT).resolve()
    candidate = (root / normalized).resolve() if normalized else root
    try:
        candidate.relative_to(root)
    except ValueError:
        raise Http404("Invalid path.")
    return candidate


def get_allowed_paths_for_user(user) -> list[str]:
    if getattr(user, "is_superuser", False):
        return [""]
    if isinstance(user, AnonymousUser):
        return []
    rules = FileAccessRule.objects.filter(group__in=user.groups.all()).values_list("path", flat=True)
    return sorted({normalize_path(path) for path in rules})


def user_has_access(user, relative_path: str) -> bool:
    if getattr(user, "is_superuser", False):
        return True
    normalized = normalize_path(relative_path)
    allowed = get_allowed_paths_for_user(user)
    if not allowed:
        return False
    # If user has a blanket rule (empty path), grant full access
    if "" in allowed:
        return True
    if normalized == "":
        return True
    return any(normalized == rule or normalized.startswith(f"{rule}/") for rule in allowed)


def filter_child_entries(user, parent_relative_path: str, entries: Iterable[Path]) -> list[Entry]:
    filtered: list[Entry] = []
    allowed = get_allowed_paths_for_user(user)
    parent_normalized = normalize_path(parent_relative_path)

    for item in entries:
        rel = normalize_path(str(Path(parent_normalized) / item.name) if parent_normalized else item.name)
        if getattr(user, "is_superuser", False) or _entry_accessible(rel, allowed):
            stat = item.stat()
            filtered.append(
                Entry(
                    name=item.name,
                    path=rel,
                    is_dir=item.is_dir(),
                    size=stat.st_size,
                    modified=stat.st_mtime,
                )
            )
    return sorted(filtered, key=lambda e: (not e.is_dir, e.name.lower()))


def _entry_accessible(rel_path: str, allowed: list[str]) -> bool:
    if not allowed:
        return False
    if rel_path == "":
        return True
    return any(
        rel_path == rule
        or rel_path.startswith(f"{rule}/")
        or rule.startswith(f"{rel_path}/")
        for rule in allowed
    )


def get_breadcrumbs(relative_path: str) -> list[tuple[str, str]]:
    normalized = normalize_path(relative_path)
    if not normalized:
        return [("Home", "")]
    parts = normalized.split("/")
    breadcrumbs = [("Home", "")]
    accum = []
    for part in parts:
        accum.append(part)
        breadcrumbs.append((part, "/".join(accum)))
    return breadcrumbs


def _format_timestamp(ts: float | int | None = None) -> str:
    """Return a compact timestamp string like 20250131_235959.

    If ts is None, use current time.
    """
    dt = datetime.datetime.fromtimestamp(ts) if ts is not None else datetime.datetime.now()
    return dt.strftime("%Y%m%d_%H%M%S")


def _compute_dir_mtime(path: Path) -> float:
    """Compute the latest modification time for a directory tree.

    Falls back to the directory's own mtime if traversal fails.
    """
    latest = path.stat().st_mtime
    try:
        for root, _dirs, files in os.walk(path):
            root_path = Path(root)
            try:
                latest = max(latest, root_path.stat().st_mtime)
            except Exception:
                pass
            for fname in files:
                fpath = root_path / fname
                try:
                    latest = max(latest, fpath.stat().st_mtime)
                except Exception:
                    continue
    except Exception:
        # Ignore traversal errors and use directory's own mtime
        pass
    return latest


def serve_file(path: Path) -> FileResponse:
    """Return a response that streams the file contents."""
    filename = path.name
    content_type, _ = mimetypes.guess_type(filename)
    response = FileResponse(open(path, "rb"), as_attachment=True, filename=filename)
    if content_type:
        response["Content-Type"] = content_type
    return response


def serve_directory(path: Path, archive_format: str = "tar.gz") -> StreamingHttpResponse:
    """Stream a compressed version of a directory without creating temp files."""
    archive_format = archive_format or "tar.gz"
    writer = QueueWriter()

    def build_archive() -> None:
        try:
            if archive_format == "zip":
                import zipfile

                with zipfile.ZipFile(writer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
                    for root, _, files in os.walk(path):
                        for file in files:
                            abs_path = Path(root) / file
                            rel_path = abs_path.relative_to(path.parent)
                            zip_file.write(abs_path, arcname=str(rel_path))
            else:
                import tarfile

                mode = "w|gz" if archive_format == "tar.gz" else "w|bz2"
                with tarfile.open(fileobj=writer, mode=mode) as tar:
                    tar.add(path, arcname=path.name)
        finally:
            writer.close()

    thread = threading.Thread(target=build_archive, daemon=True)
    thread.start()

    # Build timestamped filename based on latest modification time in the directory
    ts = _compute_dir_mtime(path)
    stamp = _format_timestamp(ts)
    base = path.name
    # Ensure proper extension
    filename = f"{base}-{stamp}.{archive_format}"
    response = StreamingHttpResponse(writer.__iter__(), content_type=_archive_mime_type(archive_format))
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


def serve_single_file_archive(path: Path, archive_format: str = "tar.gz") -> StreamingHttpResponse:
    """Stream a compressed archive containing a single file.

    The archive filename includes a timestamp suffix based on the file's last modification time.
    """
    if not path.is_file():
        raise Http404("Not a file.")

    writer = QueueWriter()

    def build_archive() -> None:
        try:
            if archive_format == "zip":
                import zipfile

                with zipfile.ZipFile(writer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
                    zip_file.write(path, arcname=path.name)
            else:
                import tarfile

                mode = "w|gz" if archive_format == "tar.gz" else "w|bz2"
                with tarfile.open(fileobj=writer, mode=mode) as tar:
                    tar.add(path, arcname=path.name)
        finally:
            writer.close()

    thread = threading.Thread(target=build_archive, daemon=True)
    thread.start()

    ts = path.stat().st_mtime
    stamp = _format_timestamp(ts)
    base = path.stem
    filename = f"{base}-{stamp}.{archive_format}"
    response = StreamingHttpResponse(writer.__iter__(), content_type=_archive_mime_type(archive_format))
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


def _archive_mime_type(fmt: str) -> str:
    return {
        "tar.gz": "application/gzip",
        "zip": "application/zip",
        "tar.bz2": "application/x-bzip2",
    }.get(fmt, "application/octet-stream")


def resolve_token(token_value: str) -> CLIToken | None:
    try:
        token = CLIToken.objects.select_related("user").get(token=token_value)
    except CLIToken.DoesNotExist:
        return None
    if not token.is_valid():
        return None
    return token


def log_download(user, relative_path: str, size: int, is_share_link: bool = False) -> None:
    from .models import DownloadLog

    DownloadLog.objects.create(user=user, path=relative_path, size=size, is_share_link=is_share_link)


def log_upload(user, relative_path: str, filename: str, size: int) -> None:
    from .models import UploadLog

    UploadLog.objects.create(user=user, path=relative_path, filename=filename, size=size)
