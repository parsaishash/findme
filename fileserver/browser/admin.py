from __future__ import annotations

from django.contrib import admin

from .models import DownloadLog, UploadLog, ProxyConfig, DownloadJob


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


@admin.register(ProxyConfig)
class ProxyConfigAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "host", "port", "is_active")
    search_fields = ("name", "host")
    list_filter = ("type", "is_active")


@admin.register(DownloadJob)
class DownloadJobAdmin(admin.ModelAdmin):
    list_display = ("job_type", "source", "target_path", "status", "created_by", "created_at")
    search_fields = ("source", "target_path", "message")
    list_filter = ("job_type", "status", "created_at")
