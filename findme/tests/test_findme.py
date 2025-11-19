from __future__ import annotations

import tempfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from browser import utils as browser_utils
from core.models import CLIToken, FileAccessRule, ShareLink
from browser.models import UploadLog

User = get_user_model()


class FindMeTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self._tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tempdir.cleanup)
        tmp_root = Path(self._tempdir.name).resolve()
        self.override = override_settings(
            FILE_SERVER_ROOT=tmp_root,
            ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
        )
        self.override.enable()
        self.addCleanup(self.override.disable)

        self.group = Group.objects.create(name="devs")
        self.user = User.objects.create_user("alice", password="SafePass123!@#")
        self.user.groups.add(self.group)
        FileAccessRule.objects.create(group=self.group, path="projects/dev")

        self.other_user = User.objects.create_user("bob", password="SafePass123!@#")

        self.file_root = Path(settings.FILE_SERVER_ROOT).resolve()
        self.base_dir = self.file_root / "projects" / "dev"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "notes.txt").write_text("hello world", encoding="utf-8")
        self.file_path = "projects/dev/notes.txt"
        self.upload_url = reverse("upload:target", kwargs={"path": "projects/dev"})

    def test_user_has_access_via_group_rule(self) -> None:
        self.assertTrue(browser_utils.user_has_access(self.user, self.file_path))
        self.assertFalse(browser_utils.user_has_access(self.other_user, self.file_path))

    def test_user_can_access_parent_directory_of_rule(self) -> None:
        self.assertTrue(browser_utils.user_has_access(self.user, "projects"))
        self.assertFalse(browser_utils.user_has_access(self.other_user, "projects"))

    def test_cli_token_generation_and_validation(self) -> None:
        token = CLIToken.create_for_user(self.user, expiry_hours=1)
        self.assertTrue(token.is_valid())
        self.assertIn(token, CLIToken.objects.active())

    def test_share_link_expiry(self) -> None:
        link = ShareLink.create_for_user(self.user, self.file_path, expiry_hours=1)
        self.assertTrue(link.is_valid())
        link.expires_at = timezone.now() - timedelta(hours=1)
        link.save(update_fields=["expires_at"])
        self.assertFalse(link.is_valid())

    def test_download_requires_permissions(self) -> None:
        self.client.login(username="alice", password="SafePass123!@#")
        url = reverse("download:file", kwargs={"path": self.file_path})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

        self.client.login(username="bob", password="SafePass123!@#")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_cli_token_can_download_without_login(self) -> None:
        token = CLIToken.create_for_user(self.user, expiry_hours=1)
        url = reverse("download:file", kwargs={"path": self.file_path})
        response = self.client.get(url, {"token": token.token})
        self.assertEqual(response.status_code, 200)

    def test_upload_rejects_unauthorized_path(self) -> None:
        self.client.login(username="bob", password="SafePass123!@#")
        url = reverse("upload:target", kwargs={"path": "secret"})
        with (Path(self._tempdir.name) / "temp.txt").open("w", encoding="utf-8") as handle:
            handle.write("data")
        with (Path(self._tempdir.name) / "temp.txt").open("rb") as fh:
            response = self.client.post(url, {"files": fh}, follow=True)
        self.assertEqual(response.status_code, 404)

    def test_upload_succeeds_for_authorized_user(self) -> None:
        self.assertTrue(self.client.login(username="alice", password="SafePass123!@#"))
        upload_file = self._make_upload_file("report.txt", b"report contents")
        response = self.client.post(
            self.upload_url,
            {"files": upload_file, "target_path": "projects/dev"},
        )
        self.assertEqual(response.status_code, 302)
        saved = self.base_dir / "report.txt"
        self.assertTrue(saved.exists())
        self.assertEqual(UploadLog.objects.count(), 1)
        self.assertTrue(saved.exists())
        self.assertEqual(saved.read_bytes(), b"report contents")

    def test_upload_returns_partial_fragment_for_htmx(self) -> None:
        self.assertTrue(self.client.login(username="alice", password="SafePass123!@#"))
        upload_file = self._make_upload_file("notes-2.txt", b"new content")
        response = self.client.post(
            self.upload_url,
            {"files": upload_file, "target_path": "projects/dev"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("<div id=\"file-list\">", html)
        self.assertIn("notes-2.txt", html)
        saved = self.base_dir / "notes-2.txt"
        self.assertTrue(saved.exists())
        self.assertEqual(saved.read_bytes(), b"new content")
        self.assertEqual(UploadLog.objects.filter(filename="notes-2.txt").count(), 1)

    def _make_upload_file(self, name: str, content: bytes) -> "SimpleUploadedFile":
        from django.core.files.uploadedfile import SimpleUploadedFile

        return SimpleUploadedFile(name, content, content_type="application/octet-stream")
