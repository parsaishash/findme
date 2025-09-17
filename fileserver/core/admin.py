from __future__ import annotations

from django.contrib import admin

from .models import CLIToken, FileAccessRule, ShareLink


@admin.register(FileAccessRule)
class FileAccessRuleAdmin(admin.ModelAdmin):
    list_display = ("group", "path")
    search_fields = ("group__name", "path")
    list_filter = ("group",)


@admin.register(CLIToken)
class CLITokenAdmin(admin.ModelAdmin):
    list_display = ("token", "user", "expires_at", "is_active")
    list_filter = ("is_active", "expires_at")
    search_fields = ("token", "user__username")
    readonly_fields = ("token", "created_at")


@admin.register(ShareLink)
class ShareLinkAdmin(admin.ModelAdmin):
    list_display = ("token", "user", "path", "expires_at", "is_active")
    list_filter = ("is_active", "expires_at")
    search_fields = ("token", "user__username", "path")
    readonly_fields = ("token", "created_at")
