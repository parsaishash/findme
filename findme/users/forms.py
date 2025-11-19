"""Forms used for superadmin user management."""
from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm
from django.contrib.auth.models import Group

User = get_user_model()


class UserCreateForm(UserCreationForm):
    """Create a new user and assign them to a group."""

    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="Optional group assignment",
    )
    is_active = forms.BooleanField(initial=True, required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for name in ("username", "password1", "password2"):
            self.fields[name].widget.attrs.update({"class": "form-control"})
        self.fields["group"].widget.attrs.setdefault("class", "form-select")
        self.fields["is_active"].widget.attrs.setdefault("class", "form-check-input")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "password1", "password2", "group", "is_active")

    def save(self, commit: bool = True) -> User:
        user = super().save(commit=False)
        user.is_active = self.cleaned_data.get("is_active", True)
        if commit:
            user.save()
            group = self.cleaned_data.get("group")
            if group:
                user.groups.set([group])
        return user


class UserGroupForm(forms.Form):
    """Assign a user to a specific group (or none)."""

    group = forms.ModelChoiceField(queryset=Group.objects.all(), required=False, widget=forms.Select(attrs={"class": "form-select form-select-sm"}))


class UserResetPasswordForm(SetPasswordForm):
    """Reset a user's password by the superadmin."""

    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
