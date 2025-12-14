"""findme URL configuration."""
from __future__ import annotations

from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings

from browser.views import HealthCheckView

# Get the root endpoint prefix from settings
root_endpoint = getattr(settings, 'ROOT_ENDPOINT', '/').strip('/')
if root_endpoint and not root_endpoint.endswith('/'):
    root_endpoint += '/'

# Create URL patterns based on root endpoint
if root_endpoint and root_endpoint != '/':
    # When using a prefix, include all URLs under that prefix
    urlpatterns = [
        re_path(rf'^{root_endpoint[:-1]}/?', include([
            path("admin/", admin.site.urls),
            path("", include("core.urls")),
            path("files/", include(("browser.urls", "browser"), namespace="browser")),
            path("download/", include(("browser.urls_download", "downloads"), namespace="download")),
            path("upload/", include(("browser.urls_upload", "uploads"), namespace="upload")),
            path("users/", include("users.urls")),
            path("health/", HealthCheckView.as_view(), name="health"),
        ])),
    ]
else:
    # Default behavior when no prefix is set
    urlpatterns = [
        path("admin/", admin.site.urls),
        path("", include("core.urls")),
        path("files/", include(("browser.urls", "browser"), namespace="browser")),
        path("download/", include(("browser.urls_download", "downloads"), namespace="download")),
        path("upload/", include(("browser.urls_upload", "uploads"), namespace="upload")),
        path("users/", include("users.urls")),
        path("health/", HealthCheckView.as_view(), name="health"),
    ]
