"""Core views including authentication, dashboard redirect, tokens, and share links."""
from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import FormView, RedirectView, TemplateView

from browser import utils as browser_utils
from browser.utils import log_download, serve_directory, serve_file
from .forms import ShareLinkForm, TokenCreateForm
from .models import CLIToken, ShareLink


class HomeRedirectView(LoginRequiredMixin, RedirectView):
    """Redirect authenticated users to the file browser."""

    permanent = False
    pattern_name = "browser:root"


class ThemedLoginView(LoginView):
    """Minimal login page following the spec."""

    template_name = "core/login.html"
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Sign in"
        return context


class ThemedLogoutView(LogoutView):
    next_page = reverse_lazy("core:login")


class ThemeToggleView(View):
    """Toggle between light and dark theme stored in the session."""

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        current = request.session.get("theme", settings.DEFAULT_THEME)
        request.session["theme"] = "dark" if current == "light" else "light"
        if request.headers.get("HX-Request") or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"theme": request.session["theme"]})
        return redirect(request.META.get("HTTP_REFERER", reverse("browser:root")))


class TokenListView(LoginRequiredMixin, TemplateView):
    """Display existing CLI tokens and provide a form to generate new ones."""

    template_name = "core/token.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["form"] = TokenCreateForm()
        context["tokens"] = CLIToken.objects.filter(user=self.request.user).order_by("-created_at")
        context["token_default_expiry"] = settings.TOKEN_EXPIRY_HOURS
        return context


class TokenCreateView(LoginRequiredMixin, FormView):
    """Generate a new CLI token for the authenticated user."""

    form_class = TokenCreateForm
    success_url = reverse_lazy("core:token")

    def form_valid(self, form: TokenCreateForm) -> HttpResponse:
        token = CLIToken.create_for_user(self.request.user, expiry_hours=form.get_expiry())
        base_url = self.request.build_absolute_uri("/").rstrip("/")
        data = {
            "token": token.token,
            "expires_at": token.expires_at,
            "curl_example": f"curl -O {base_url}/download/file/<path>?token={token.token}",
            "wget_example": f"wget {base_url}/download/file/<path>?token={token.token}",
        }
        if self._wants_json():
            return JsonResponse({"success": True, **data})
        messages.success(self.request, _("Token generated."))
        return redirect(self.get_success_url())

    def form_invalid(self, form: TokenCreateForm) -> HttpResponse:
        if self._wants_json():
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
        messages.error(self.request, _("Unable to generate token."))
        return redirect(self.get_success_url())

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["data"] = self.request.POST or None
        return kwargs

    def _wants_json(self) -> bool:
        accept = self.request.headers.get("Accept", "")
        requested_with = self.request.headers.get("X-Requested-With")
        return "application/json" in accept or requested_with == "XMLHttpRequest"


class TokenRevokeView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Revoke a CLI token belonging to the requesting user."""

    def test_func(self) -> bool:
        token = self.get_object()
        return token.user == self.request.user or self.request.user.is_superuser

    def get_object(self) -> CLIToken:
        try:
            return CLIToken.objects.get(token=self.kwargs["token"])
        except CLIToken.DoesNotExist as exc:
            raise Http404("Token not found.") from exc

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        token = self.get_object()
        token.revoke()
        if request.headers.get("Accept", "").startswith("application/json"):
            return JsonResponse({"success": True})
        messages.success(request, _("Token revoked."))
        return redirect(reverse("core:token"))


class ShareLinkCreateView(LoginRequiredMixin, FormView):
    """Create a share link for a file or folder."""

    form_class = ShareLinkForm
    http_method_names = ["post"]

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["data"] = self.request.POST or None
        return kwargs

    def form_valid(self, form: ShareLinkForm) -> HttpResponse:
        path = form.cleaned_data["path"]
        expiry = form.get_expiry()
        link = ShareLink.create_for_user(self.request.user, path, expiry_hours=expiry)
        absolute_url = self.request.build_absolute_uri(reverse("core:share", args=[link.token]))
        data = {
            "success": True,
            "token": link.token,
            "url": absolute_url,
            "expires_at": link.expires_at,
        }
        if self._wants_json():
            return JsonResponse(data)
        messages.success(self.request, _("Share link created."))
        return redirect(reverse("browser:root"))

    def form_invalid(self, form: ShareLinkForm) -> HttpResponse:
        if self._wants_json():
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
        messages.error(self.request, _("Unable to create share link."))
        return redirect(reverse("browser:root"))

    def _wants_json(self) -> bool:
        accept = self.request.headers.get("Accept", "")
        requested_with = self.request.headers.get("X-Requested-With")
        return "application/json" in accept or requested_with == "XMLHttpRequest"


class ShareLinkRevokeView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Allow the owner (or superadmin) to revoke a share link."""

    def get_object(self) -> ShareLink:
        try:
            return ShareLink.objects.get(token=self.kwargs["token"])
        except ShareLink.DoesNotExist as exc:
            raise Http404("Share link not found.") from exc

    def test_func(self) -> bool:
        link = self.get_object()
        return link.user == self.request.user or self.request.user.is_superuser

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        link = self.get_object()
        link.revoke()
        if request.headers.get("Accept", "").startswith("application/json"):
            return JsonResponse({"success": True})
        messages.success(request, _("Share link revoked."))
        return redirect(reverse("browser:root"))


class ShareLinkView(TemplateView):
    """Public view to access a shared file or folder."""

    template_name = "core/share.html"

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.share_link = self.get_share_link()
        self.target_path = browser_utils.resolve_target_path(self.share_link.path)
        if not self.target_path.exists():
            raise Http404("Shared item no longer exists.")
        if self._is_download_request():
            return self._handle_download()
        return super().dispatch(request, *args, **kwargs)

    def get_share_link(self) -> ShareLink:
        try:
            link = ShareLink.objects.get(token=self.kwargs["token"])
        except ShareLink.DoesNotExist as exc:
            raise Http404("Share link not found.") from exc
        if not link.is_valid():
            raise Http404("This share link has expired.")
        return link

    def _is_download_request(self) -> bool:
        return "download" in self.request.GET or "format" in self.request.GET

    def _handle_download(self) -> HttpResponse:
        if self.target_path.is_file():
            response = serve_file(self.target_path)
            log_download(None, self.share_link.path, self.target_path.stat().st_size, is_share_link=True)
            return response
        archive_format = self.request.GET.get("format", "tar.gz")
        response = serve_directory(self.target_path, archive_format=archive_format)
        log_download(None, self.share_link.path, 0, is_share_link=True)
        return response

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        is_dir = self.target_path.is_dir()
        entries = []
        if is_dir:
            for item in sorted(self.target_path.iterdir(), key=lambda i: (not i.is_dir(), i.name.lower())):
                stat = item.stat()
                entries.append(
                    {
                        "name": item.name,
                        "is_dir": item.is_dir(),
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                    }
                )
        base_url = self.request.build_absolute_uri(reverse("core:share", args=[self.share_link.token]))
        context.update(
            {
                "link": self.share_link,
                "is_dir": is_dir,
                "entries": entries,
                "download_url": f"{base_url}?{urlencode({'download': 1})}",
                "zip_url": f"{base_url}?{urlencode({'format': 'zip'})}",
                "token": self.share_link.token,
            }
        )
        return context


class NotFoundView(TemplateView):
    """Simple 404 page for share link expirations."""

    template_name = "core/404.html"
