"""Core models for authentication helpers, tokens, and share links."""
from __future__ import annotations

import secrets
from datetime import timedelta
from pathlib import PurePosixPath

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import models
from django.utils import timezone

User = get_user_model()


def _normalize_path(value: str) -> str:
    return str(PurePosixPath("/" + value.strip("/"))).lstrip("/")


class FileAccessRule(models.Model):
    """Map a Django group to a folder path relative to FILE_SERVER_ROOT."""

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="file_access_rules")
    path = models.CharField(max_length=512, help_text="Relative path from FILE_SERVER_ROOT without leading slash")

    class Meta:
        unique_together = ("group", "path")
        ordering = ["group__name", "path"]

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return f"{self.group.name}: {self.path}" if self.group_id else self.path

    def save(self, *args, **kwargs) -> None:  # pragma: no cover - normalization only
        self.path = _normalize_path(self.path)
        super().save(*args, **kwargs)


class TokenQuerySet(models.QuerySet):
    def active(self) -> "TokenQuerySet":
        return self.filter(is_active=True, expires_at__gt=timezone.now())


class CLIToken(models.Model):
    """Temporary token that grants CLI access within a user's permissions."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cli_tokens")
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    objects = TokenQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return f"{self.token} ({self.user})"

    @classmethod
    def generate_token(cls, length: int = 16) -> str:
        """Generate a short, URL-safe token string."""
        return secrets.token_urlsafe(length)[:length]

    @classmethod
    def create_for_user(cls, user: User, expiry_hours: int | None = None) -> "CLIToken":
        expiry = timezone.now() + timedelta(hours=expiry_hours or settings.TOKEN_EXPIRY_HOURS)
        token_value = cls.generate_token()
        while cls.objects.filter(token=token_value).exists():
            token_value = cls.generate_token()
        return cls.objects.create(user=user, token=token_value, expires_at=expiry)

    def is_valid(self) -> bool:
        return self.is_active and self.expires_at > timezone.now()

    def revoke(self) -> None:
        self.is_active = False
        self.save(update_fields=["is_active"])


class ShareLink(models.Model):
    """Temporary share link for a file or folder."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="share_links")
    token = models.CharField(max_length=64, unique=True)
    path = models.CharField(max_length=512, help_text="Relative path to the shared asset")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    objects = TokenQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return f"ShareLink({self.token})"

    @classmethod
    def generate_token(cls, length: int = 32) -> str:
        return secrets.token_urlsafe(length)

    @classmethod
    def create_for_user(cls, user: User, path: str, expiry_hours: int | None = None) -> "ShareLink":
        expiry = timezone.now() + timedelta(hours=expiry_hours or settings.SHARE_LINK_EXPIRY_HOURS)
        token_value = cls.generate_token()
        while cls.objects.filter(token=token_value).exists():
            token_value = cls.generate_token()
        return cls.objects.create(user=user, path=_normalize_path(path), token=token_value, expires_at=expiry)

    def is_valid(self) -> bool:
        return self.is_active and self.expires_at > timezone.now()

    def revoke(self) -> None:
        self.is_active = False
        self.save(update_fields=["is_active"])
