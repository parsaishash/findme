"""Forms for browser operations like uploads."""
from __future__ import annotations

from django import forms


class UploadForm(forms.Form):
    """Upload one or more files into the requested directory."""

    target_path = forms.CharField(widget=forms.HiddenInput())

    def clean_target_path(self) -> str:
        from . import utils

        return utils.normalize_path(self.cleaned_data["target_path"])
