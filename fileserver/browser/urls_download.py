"""URL patterns for download endpoints."""
from __future__ import annotations

from django.urls import path

from . import views

app_name = "downloads"

urlpatterns = [
    path("file/<path:path>/", views.DownloadFileView.as_view(), name="file"),
    path("folder/<path:path>/", views.DownloadFolderView.as_view(), name="folder"),
]
