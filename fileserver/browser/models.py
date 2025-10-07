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


class ProxyConfig(models.Model):
    """Reusable proxy configuration accessible to users when creating download jobs."""

    PROXY_TYPES = (
        ("socks5", "SOCKS5"),
        ("http", "HTTP"),
        ("https", "HTTPS"),
    )

    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=10, choices=PROXY_TYPES, default="socks5")
    host = models.CharField(max_length=255)
    port = models.IntegerField(default=1080)
    username = models.CharField(max_length=128, blank=True)
    password = models.CharField(max_length=128, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.name} ({self.type}://{self.host}:{self.port})"

    def as_requests_dict(self) -> dict:
        auth = f"{self.username}:{self.password}@" if self.username and self.password else ""
        base = f"{self.type}://{auth}{self.host}:{self.port}"
        return {"http": base, "https": base}


class DownloadJob(models.Model):
    """Track background download/import jobs (URL, Git, Docker image)."""

    TYPE_URL = "url"
    TYPE_GIT = "git"
    TYPE_DOCKER = "docker"
    TYPES = (
        (TYPE_URL, "URL Download"),
        (TYPE_GIT, "Git Clone"),
        (TYPE_DOCKER, "Docker Image"),
    )

    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUSES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_RUNNING, "Running"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    job_type = models.CharField(max_length=16, choices=TYPES)
    source = models.CharField(max_length=1024, help_text="URL, repo, or docker image ref")
    target_path = models.CharField(max_length=512, help_text="Relative path under FILE_SERVER_ROOT")
    proxy = models.ForeignKey(ProxyConfig, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=16, choices=STATUSES, default=STATUS_PENDING)
    message = models.TextField(blank=True)
    result_path = models.CharField(max_length=1024, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.job_type}:{self.source} -> {self.target_path} [{self.status}]"

