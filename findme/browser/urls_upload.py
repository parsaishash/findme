"""URL patterns for upload endpoints."""
from __future__ import annotations

from django.urls import path

from . import views

app_name = "uploads"

urlpatterns = [
    path("<path:path>/", views.UploadView.as_view(), name="target"),
    path("", views.UploadView.as_view(), name="root"),
]
