"""URL patterns for core app."""
from __future__ import annotations

from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeRedirectView.as_view(), name="home"),
    path("login/", views.ThemedLoginView.as_view(), name="login"),
    path("logout/", views.ThemedLogoutView.as_view(), name="logout"),
    path("theme/toggle/", views.ThemeToggleView.as_view(), name="theme-toggle"),
    path("token/", views.TokenListView.as_view(), name="token"),
    path("token/new/", views.TokenCreateView.as_view(), name="token-create"),
    path("token/<str:token>/revoke/", views.TokenRevokeView.as_view(), name="token-revoke"),
    path("share/create/", views.ShareLinkCreateView.as_view(), name="share-create"),
    path("share/<str:token>/", views.ShareLinkView.as_view(), name="share"),
    path("share/<str:token>/revoke/", views.ShareLinkRevokeView.as_view(), name="share-revoke"),
]
