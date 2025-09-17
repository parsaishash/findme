"""Optional logging models for uploads and downloads."""
from __future__ import annotations

from django.conf import settings
from django.db import models


class TimestampedModel(models.Model):
    """Abstract base model with created timestamp."""

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class UploadLog(TimestampedModel):
    """Track file uploads for auditing purposes."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    path = models.CharField(max_length=512)
    filename = models.CharField(max_length=255)
    size = models.BigIntegerField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"Upload {self.filename} ({self.size} bytes)"


class DownloadLog(TimestampedModel):
    """Track file downloads for auditing purposes."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    path = models.CharField(max_length=512)
    is_share_link = models.BooleanField(default=False)
    size = models.BigIntegerField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"Download {self.path}"
