"""Wagtail authorization policy for editor-managed push notifications."""

from __future__ import annotations

from collections.abc import Iterable

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.db.models import QuerySet
from wagtail.permission_policies.base import BaseDjangoAuthPermissionPolicy

from .models import PushNotification


class PushNotificationPermissionPolicy(BaseDjangoAuthPermissionPolicy):
    """Allow notification viewing, creation, and editing through one permission.

    Wagtail asks its policy about CRUD-style action names, but notification
    dispatch is intentionally administered as one capability rather than a
    collection of independently assignable model permissions.
    """

    permission_codename = "manage_push_notifications"
    allowed_actions = frozenset({"add", "change", "view"})

    def check_model(self, model: type[PushNotification]) -> None:
        """Reject accidental reuse of this policy for another model."""

        if model is not PushNotification:
            raise ImproperlyConfigured(
                "PushNotificationPermissionPolicy only supports PushNotification."
            )

    def user_has_permission(
        self, user: AbstractBaseUser | AnonymousUser, action: str
    ) -> bool:
        """Return whether an active user may perform a notification action."""

        if action not in self.allowed_actions:
            return False
        return user.has_perm(f"{self.app_label}.{self.permission_codename}")

    def users_with_any_permission(
        self, actions: Iterable[str]
    ) -> QuerySet[AbstractBaseUser]:
        """Return active users with the custom permission from users or groups."""

        if not self.allowed_actions.intersection(actions):
            return get_user_model().objects.none()
        return self._get_users_with_any_permission_codenames(
            {self.permission_codename}
        )
