"""Forms for CLI tokens and share links."""
from __future__ import annotations

from django import forms
from django.conf import settings

from browser import utils as browser_utils


class TokenCreateForm(forms.Form):
    """Form to generate a CLI token with optional custom expiry."""

    expiry_hours = forms.IntegerField(
        min_value=1,
        required=False,
        label="Expiry (hours)",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": settings.TOKEN_EXPIRY_HOURS}),
    )

    def get_expiry(self) -> int:
        return self.cleaned_data.get("expiry_hours") or settings.TOKEN_EXPIRY_HOURS


class ShareLinkForm(forms.Form):
    """Form to create a share link for a file or folder."""

    path = forms.CharField(widget=forms.HiddenInput())
    expiry_hours = forms.IntegerField(
        min_value=1,
        required=False,
        label="Expiry (hours)",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": settings.SHARE_LINK_EXPIRY_HOURS}),
    )

    def __init__(self, *args, **kwargs) -> None:
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean_path(self) -> str:
        value = self.cleaned_data["path"]
        normalized = browser_utils.normalize_path(value)
        if not browser_utils.user_has_access(self.user, normalized):
            raise forms.ValidationError("You do not have access to this path.")
        return normalized

    def get_expiry(self) -> int:
        return self.cleaned_data.get("expiry_hours") or settings.SHARE_LINK_EXPIRY_HOURS
