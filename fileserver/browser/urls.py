"""URL patterns for browsing files."""
from __future__ import annotations

from django.urls import path

from . import views

app_name = "browser"

urlpatterns = [
    path("", views.FileBrowserView.as_view(), name="root"),
    path("<path:path>/", views.FileBrowserView.as_view(), name="browse"),
]
