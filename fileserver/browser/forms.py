"""Forms for browser operations like uploads."""
from __future__ import annotations

from django import forms


class MultiFileInput(forms.ClearableFileInput):
    """Clearable file input that allows selecting multiple files."""

    allow_multiple_selected = True


class UploadForm(forms.Form):
    """Upload one or more files into the requested directory."""

    target_path = forms.CharField(widget=forms.HiddenInput())
    files = forms.FileField(
        widget=MultiFileInput(attrs={"multiple": True, "class": "form-control"}),
        label="Select files",
    )

    def clean_target_path(self) -> str:
        from . import utils

        return utils.normalize_path(self.cleaned_data["target_path"])
