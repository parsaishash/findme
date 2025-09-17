"""URL patterns for user management."""
from __future__ import annotations

from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("", views.UserManagementView.as_view(), name="manage"),
    path("create/", views.UserCreateView.as_view(), name="create"),
    path("<int:pk>/group/", views.UserGroupUpdateView.as_view(), name="update-group"),
    path("<int:pk>/toggle/", views.UserToggleActiveView.as_view(), name="toggle"),
    path("<int:pk>/delete/", views.UserDeleteView.as_view(), name="delete"),
    path("<int:pk>/reset-password/", views.UserResetPasswordView.as_view(), name="reset-password"),
]
