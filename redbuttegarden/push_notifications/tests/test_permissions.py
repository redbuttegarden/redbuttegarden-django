"""Authorization regressions for the notification Wagtail viewset."""

from __future__ import annotations

from django.contrib.auth.models import Group, Permission
from django.http import HttpResponseBase
from django.test import Client, TestCase
from django.urls import reverse
from wagtail.test.utils import WagtailTestUtils

from push_notifications.models import PushNotification
from push_notifications.wagtail_hooks import PushNotificationViewSet


class PushNotificationAuthorizationTests(WagtailTestUtils, TestCase):
    """Prove that only notification managers can use the Wagtail feature."""

    def setUp(self) -> None:
        """Create users representing each permission path and denial case."""

        self.manage_perm = Permission.objects.get(
            content_type__app_label="push_notifications",
            content_type__model="pushnotification",
            codename="manage_push_notifications",
        )
        self.admin_access_perm = Permission.objects.get(codename="access_admin")
        self.inactive_user = self.create_user(
            username="inactive", password="pw", is_active=False
        )
        self.no_permission_user = self.create_user(username="no-permission", password="pw")
        self.no_permission_user.user_permissions.add(self.admin_access_perm)
        self.legacy_crud_user = self.create_user(username="legacy", password="pw")
        self.legacy_crud_user.user_permissions.add(
            self.admin_access_perm,
            Permission.objects.get(
                content_type__app_label="push_notifications",
                content_type__model="pushnotification",
                codename="add_pushnotification",
            ),
        )
        self.direct_grant_user = self.create_user(username="direct", password="pw")
        self.direct_grant_user.user_permissions.add(
            self.admin_access_perm, self.manage_perm
        )
        self.group_grant_user = self.create_user(username="group", password="pw")
        self.group_grant_user.user_permissions.add(self.admin_access_perm)
        managers = Group.objects.create(name="Push Managers")
        managers.permissions.add(self.manage_perm)
        self.group_grant_user.groups.add(managers)
        self.superuser = self.create_superuser(username="super", password="pw")
        self.list_url = reverse("wagtailsnippets_push_notifications_pushnotification:list")
        self.add_url = reverse("wagtailsnippets_push_notifications_pushnotification:add")

    def bulk_delete_url(self, notification: PushNotification) -> str:
        """Return Wagtail's generic bulk-delete URL for a notification id."""

        return (
            reverse(
                "wagtail_bulk_action",
                args=["push_notifications", "pushnotification", "delete"],
            )
            + f"?id={notification.pk}"
        )

    def deleted_notification_url(self, notification: PushNotification) -> str:
        """Return the former single-delete path, which must no longer resolve."""

        return (
            "/admin/snippets/push_notifications/pushnotification/delete/"
            f"{notification.pk}/"
        )

    def notification_data(self, title: str) -> dict[str, str]:
        """Return a complete valid Wagtail notification create request."""

        return {
            "title": title,
            "body": "The Garden has an update for subscribers.",
            "icon_path": "",
            "destination_path": "/events",
            "scheduled_time": "",
            "action-save-draft": "1",
        }

    def assert_admin_login_redirect(
        self, response: HttpResponseBase, target_url: str
    ) -> None:
        """Assert Wagtail redirects inactive users to login with the requested URL."""

        self.assertRedirects(
            response,
            f"{reverse('wagtailadmin_login')}?next={target_url}",
            fetch_redirect_response=False,
        )

    def assert_admin_home_redirect(self, response: HttpResponseBase) -> None:
        """Assert Wagtail redirects an authenticated unauthorized user to admin home."""

        self.assertRedirects(
            response,
            reverse("wagtailadmin_home"),
            fetch_redirect_response=False,
        )

    def test_only_manage_permission_is_registered_for_groups(self) -> None:
        """Expose the custom capability, not misleading CRUD permissions, in Groups UI."""

        permissions = PushNotificationViewSet().get_permissions_to_register()

        self.assertEqual(
            list(permissions.values_list("codename", flat=True)),
            ["manage_push_notifications"],
        )
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("wagtailusers_groups:add"))
        self.assertContains(response, "Can manage push notifications")
        self.assertNotContains(response, "Can add push notification")

    def test_denied_users_receive_exact_admin_denials_in_fresh_sessions(self) -> None:
        """Deny inactive, unprivileged, and legacy CRUD users without session bleed."""

        for user in (self.inactive_user, self.no_permission_user, self.legacy_crud_user):
            self.client.logout()
            self.client.force_login(user)

            if user == self.inactive_user:
                self.assert_admin_login_redirect(self.client.get(self.list_url), self.list_url)
                self.assert_admin_login_redirect(
                    self.client.post(self.add_url, self.notification_data("Denied")),
                    self.add_url,
                )
            else:
                self.assert_admin_home_redirect(self.client.get(self.list_url))
                self.assert_admin_home_redirect(
                    self.client.post(self.add_url, self.notification_data("Denied"))
                )
            self.assertFalse(PushNotification.objects.filter(title="Denied").exists())

    def test_anonymous_user_is_redirected_to_admin_login(self) -> None:
        """Keep Wagtail's unauthenticated redirect separate from authorization denials."""

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("wagtailadmin_login"), response.url)

    def test_manage_permission_allows_direct_group_and_superuser_creation(self) -> None:
        """Allow custom permission grants from users, groups, and superuser status."""

        for user in (self.direct_grant_user, self.group_grant_user, self.superuser):
            self.client.logout()
            self.client.force_login(user)
            title = f"Valid {user.username}"

            self.assertEqual(self.client.get(self.list_url).status_code, 200)
            response = self.client.post(self.add_url, self.notification_data(title))

            self.assertRedirects(response, self.list_url, fetch_redirect_response=False)
            self.assertTrue(PushNotification.objects.filter(title=title).exists())

    def test_notifications_menu_is_visible_only_to_notification_managers(self) -> None:
        """Show the top-level menu item only when its policy grants access."""

        self.client.force_login(self.no_permission_user)
        self.assertNotContains(self.client.get(reverse("wagtailadmin_home")), "Notifications")
        self.client.logout()
        self.client.force_login(self.group_grant_user)
        self.assertContains(self.client.get(reverse("wagtailadmin_home")), "Notifications")

    def test_manager_can_edit_but_cannot_delete_notification_history(self) -> None:
        """Retain notification and delivery audit history even for managers."""

        notification = PushNotification.objects.create(title="History", body="Retain me")
        edit_url = reverse(
            "wagtailsnippets_push_notifications_pushnotification:edit",
            args=[notification.pk],
        )
        self.client.force_login(self.direct_grant_user)
        self.assertEqual(self.client.get(edit_url).status_code, 200)
        self.assertRedirects(
            self.client.post(edit_url, self.notification_data("Updated history")),
            self.list_url,
            fetch_redirect_response=False,
        )
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.direct_grant_user)
        self.assertEqual(
            csrf_client.post(edit_url, self.notification_data("Forged update")).status_code,
            403,
        )
        self.assertEqual(self.client.get(self.deleted_notification_url(notification)).status_code, 404)
        self.assertEqual(self.client.post(self.deleted_notification_url(notification)).status_code, 404)
        self.assertEqual(self.client.get(self.bulk_delete_url(notification)).status_code, 404)
        self.assertEqual(self.client.post(self.bulk_delete_url(notification)).status_code, 404)
        self.assertTrue(PushNotification.objects.filter(pk=notification.pk).exists())

    def test_legacy_and_unprivileged_users_cannot_mutate_or_delete_history(self) -> None:
        """Deny edit, deleted-route, and bulk-delete URLs in isolated sessions."""

        notification = PushNotification.objects.create(title="Protected", body="Retain me")
        edit_url = reverse(
            "wagtailsnippets_push_notifications_pushnotification:edit",
            args=[notification.pk],
        )
        for user in (self.no_permission_user, self.legacy_crud_user):
            self.client.logout()
            self.client.force_login(user)
            self.assert_admin_home_redirect(self.client.get(edit_url))
            self.assert_admin_home_redirect(
                self.client.post(edit_url, self.notification_data("Unauthorized update"))
            )
            self.assertEqual(self.client.get(self.deleted_notification_url(notification)).status_code, 404)
            self.assertEqual(self.client.post(self.deleted_notification_url(notification)).status_code, 404)
            self.assertEqual(self.client.get(self.bulk_delete_url(notification)).status_code, 404)
            self.assertEqual(self.client.post(self.bulk_delete_url(notification)).status_code, 404)
        self.assertTrue(PushNotification.objects.filter(pk=notification.pk).exists())
