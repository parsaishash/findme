"""Views for browsing, downloading, and uploading files."""
from __future__ import annotations

from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import FormView, TemplateView

from core.models import CLIToken
from .forms import UploadForm
from . import utils


class FileBrowserView(LoginRequiredMixin, TemplateView):
    """Display contents of a directory the user has access to."""

    template_name = "browser/file_list.html"

    def get_relative_path(self) -> str:
        return self.kwargs.get("path", "")

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        relative_path = self.get_relative_path()
        if not utils.user_has_access(request.user, relative_path):
            raise Http404("You do not have access to this directory.")
        self.target_path = utils.resolve_target_path(relative_path)
        if not self.target_path.exists() or not self.target_path.is_dir():
            raise Http404("Directory not found.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        relative_path = self.get_relative_path()
        entries = utils.filter_child_entries(self.request.user, relative_path, self.target_path.iterdir())
        breadcrumbs = utils.get_breadcrumbs(relative_path)
        context.update(
            {
                "entries": entries,
                "breadcrumbs": breadcrumbs,
                "current_path": relative_path,
                "upload_form": UploadForm(initial={"target_path": relative_path}),
                "can_navigate_up": relative_path != "",
                "parent_path": "/".join(relative_path.split("/")[:-1]) if relative_path else "",
                "share_default_expiry": settings.SHARE_LINK_EXPIRY_HOURS,
                "token_default_expiry": settings.TOKEN_EXPIRY_HOURS,
            }
        )
        return context


class TokenOrLoginRequiredMixin(View):
    """Allow access via login session or CLI token query parameter."""

    token_param = "token"
    cli_token: CLIToken | None = None

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        token_value = request.GET.get(self.token_param) or request.headers.get("X-Auth-Token")
        if token_value:
            token = utils.resolve_token(token_value)
            if token is None:
                raise Http404("Invalid or expired token.")
            self.cli_token = token
        else:
            self.cli_token = None
        if not (self.cli_token or request.user.is_authenticated):
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)

    def get_effective_user(self):
        return self.cli_token.user if self.cli_token else self.request.user

    def get_logging_user(self):
        user = self.get_effective_user()
        return user if getattr(user, "is_authenticated", False) else None


class DownloadFileView(TokenOrLoginRequiredMixin, View):
    """Stream a file download to the client."""

    def get(self, request: HttpRequest, path: str) -> HttpResponse:
        relative_path = path
        user = self.get_effective_user()
        if not utils.user_has_access(user, relative_path):
            raise Http404("You do not have access to this file.")
        target = utils.resolve_target_path(relative_path)
        if not target.exists() or not target.is_file():
            raise Http404("File not found.")
        response = utils.serve_file(target)
        utils.log_download(self.get_logging_user(), relative_path, target.stat().st_size, is_share_link=False)
        return response


class DownloadFolderView(TokenOrLoginRequiredMixin, View):
    """Stream a compressed folder download."""

    def get(self, request: HttpRequest, path: str) -> HttpResponse:
        relative_path = path
        user = self.get_effective_user()
        if not utils.user_has_access(user, relative_path):
            raise Http404("You do not have access to this folder.")
        target = utils.resolve_target_path(relative_path)
        if not target.exists() or not target.is_dir():
            raise Http404("Folder not found.")
        archive_format = request.GET.get("format", "tar.gz")
        response = utils.serve_directory(target, archive_format=archive_format)
        utils.log_download(self.get_logging_user(), relative_path, 0, is_share_link=False)
        return response


class UploadView(LoginRequiredMixin, FormView):
    """Handle file uploads through the browser or CLI."""

    form_class = UploadForm
    http_method_names = ["post"]

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:  # noqa: D401
        """Restrict dispatch to POST requests."""
        if request.method.lower() != "post":
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form: UploadForm) -> HttpResponse:
        if self._wants_json():
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
        messages.error(self.request, _("Unable to upload files."))
        return self._redirect_response(form.cleaned_data.get("target_path", ""))

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        data = kwargs.get("data").copy() if kwargs.get("data") else self.request.POST.copy()
        data.setdefault("target_path", self.kwargs.get("path", ""))
        kwargs["data"] = data
        kwargs["files"] = self.request.FILES if self.request.FILES else None
        return kwargs

    def form_valid(self, form: UploadForm) -> HttpResponse:
        relative_path = form.cleaned_data["target_path"]
        if not utils.user_has_access(self.request.user, relative_path):
            raise Http404("You do not have access to this location.")
        target_dir = utils.resolve_target_path(relative_path)
        if not target_dir.exists():
            raise Http404("Upload destination does not exist.")
        if not target_dir.is_dir():
            raise Http404("Cannot upload into a file.")

        uploaded_files = self.request.FILES.getlist("files") or self.request.FILES.getlist("file")
        if not uploaded_files:
            raise Http404("No files provided.")

        saved = []
        for uploaded in uploaded_files:
            destination = target_dir / uploaded.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("wb") as dest:
                for chunk in uploaded.chunks():
                    dest.write(chunk)
            utils.log_upload(self.request.user, relative_path, uploaded.name, uploaded.size)
            saved.append(uploaded.name)

        if self._wants_partial():
            # Re-render the entries fragment for HTMX swap
            target_dir = utils.resolve_target_path(relative_path)
            entries = utils.filter_child_entries(self.request.user, relative_path, target_dir.iterdir())
            html = render_to_string(
                "browser/_entries.html",
                {"entries": entries},
                request=self.request,
            )
            return HttpResponse(f'<div id="file-list">{html}</div>')
        if self._wants_json():
            return JsonResponse({"success": True, "files": saved})
        messages.success(self.request, _("Uploaded %(count)s file(s).") % {"count": len(saved)})
        return self._redirect_response(relative_path)

    def _wants_json(self) -> bool:
        accept = self.request.headers.get("Accept", "")
        requested_with = self.request.headers.get("X-Requested-With")
        return "application/json" in accept or requested_with == "XMLHttpRequest"

    def _wants_partial(self) -> bool:
        # Prefer HTMX full fragment return for browser list refresh
        return self.request.headers.get("HX-Request") == "true"

    def _redirect_response(self, relative_path: str) -> HttpResponse:
        target = relative_path or ""
        url = reverse("browser:root") if not target else reverse("browser:browse", kwargs={"path": target})
        return redirect(url)


class HealthCheckView(View):
    """Simple health check endpoint for readiness probes."""

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return JsonResponse({"status": "ok"})
