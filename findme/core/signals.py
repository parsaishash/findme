from __future__ import annotations

import os
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import FileAccessRule

User = get_user_model()


def _user_home_relative(user: User) -> str:
    # Home path under FILE_SERVER_ROOT, e.g., users/<username>
    return f"users/{user.username}"


@receiver(post_save, sender=User)
def create_user_home_and_rule(sender, instance: User, created: bool, **kwargs):  # pragma: no cover - side effect
    if not created:
        return
    base = Path(settings.FILE_SERVER_ROOT).resolve()
    home_rel = _user_home_relative(instance)
    home_abs = (base / home_rel).resolve()
    try:
        home_abs.mkdir(parents=True, exist_ok=True)
    except Exception:
        # If FS not ready, skip silently
        return

    # Ensure a per-user group exists to manage access, e.g., user-alice
    group_name = f"user-{instance.username}"
    group, _ = Group.objects.get_or_create(name=group_name)
    instance.groups.add(group)

    # Create default access rule for the user's home
    FileAccessRule.objects.get_or_create(group=group, path=home_rel)


