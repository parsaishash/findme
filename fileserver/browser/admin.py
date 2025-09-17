from __future__ import annotations

from django.contrib import admin

from .models import DownloadLog, UploadLog


@admin.register(UploadLog)
class UploadLogAdmin(admin.ModelAdmin):
    list_display = ("filename", "path", "user", "size", "created_at")
    search_fields = ("filename", "path", "user__username")
    list_filter = ("created_at",)


@admin.register(DownloadLog)
class DownloadLogAdmin(admin.ModelAdmin):
    list_display = ("path", "user", "size", "is_share_link", "created_at")
    search_fields = ("path", "user__username")
    list_filter = ("is_share_link", "created_at")
