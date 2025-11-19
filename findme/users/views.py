"""Views for superadmin user management."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import FormView, TemplateView

from .forms import UserCreateForm, UserGroupForm, UserResetPasswordForm

User = get_user_model()


class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Ensure the requesting user is a superuser."""

    def test_func(self) -> bool:
        return self.request.user.is_superuser

    def handle_no_permission(self) -> HttpResponse:
        if self.request.user.is_authenticated:
            raise Http404("Not permitted")
        return super().handle_no_permission()


class UserManagementView(SuperuserRequiredMixin, TemplateView):
    """Render the management dashboard for superadmins."""

    template_name = "users/manage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create_form"] = UserCreateForm()
        context["groups"] = Group.objects.all().order_by("name")
        context["users_list"] = (
            User.objects.all()
            .select_related()
            .prefetch_related("groups")
            .order_by("username")
        )
        return context


class UserCreateView(SuperuserRequiredMixin, FormView):
    """Create a new user from the modal form."""

    form_class = UserCreateForm
    template_name = "users/manage.html"

    def form_valid(self, form: UserCreateForm) -> HttpResponse:
        user = form.save()
        messages.success(self.request, _("User '%(username)s' created.") % {"username": user.username})
        return redirect(reverse("users:manage"))

    def form_invalid(self, form: UserCreateForm) -> HttpResponse:
        messages.error(self.request, _("Could not create the user."))
        return redirect(reverse("users:manage"))


class UserGroupUpdateView(SuperuserRequiredMixin, View):
    """Assign the target user to a new group."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        user = get_object_or_404(User, pk=pk)
        form = UserGroupForm(request.POST)
        if form.is_valid():
            group = form.cleaned_data["group"]
            if group:
                user.groups.set([group])
                messages.success(request, _("Updated groups for %(username)s.") % {"username": user.username})
            else:
                user.groups.clear()
                messages.success(request, _("Removed groups for %(username)s.") % {"username": user.username})
        else:
            messages.error(request, _("Unable to update groups."))
        return redirect(reverse("users:manage"))


class UserToggleActiveView(SuperuserRequiredMixin, View):
    """Activate or deactivate a user."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, _("You cannot deactivate your own account."))
            return redirect(reverse("users:manage"))
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        state = "activated" if user.is_active else "deactivated"
        messages.success(request, _("User %(username)s %(state)s.") % {"username": user.username, "state": state})
        return redirect(reverse("users:manage"))


class UserDeleteView(SuperuserRequiredMixin, View):
    """Delete a user account."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, _("You cannot delete yourself."))
            return redirect(reverse("users:manage"))
        username = user.username
        user.delete()
        messages.success(request, _("User %(username)s deleted.") % {"username": username})
        return redirect(reverse("users:manage"))


class UserResetPasswordView(SuperuserRequiredMixin, View):
    """Set a new password for a user."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        user = get_object_or_404(User, pk=pk)
        form = UserResetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Password reset for %(username)s.") % {"username": user.username})
        else:
            messages.error(request, _("Unable to reset password."))
        return redirect(reverse("users:manage"))
