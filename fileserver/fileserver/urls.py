"""fileserver URL Configuration."""
from __future__ import annotations

from django.contrib import admin
from django.urls import include, path

from browser.views import HealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("files/", include(("browser.urls", "browser"), namespace="browser")),
    path("download/", include(("browser.urls_download", "downloads"), namespace="download")),
    path("upload/", include(("browser.urls_upload", "uploads"), namespace="upload")),
    path("users/", include("users.urls")),
    path("health/", HealthCheckView.as_view(), name="health"),
]
