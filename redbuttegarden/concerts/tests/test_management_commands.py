from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock

from django.core.management import call_command

from concerts.models import OAuth2Token


def test_deactivate_cdc_members_marks_only_active_members_inactive(
    create_user,
    create_cdc_member,
    settings,
):
    settings.DEBUG = True
    active_member = create_cdc_member(user=create_user(username="active-member"), active=True)
    inactive_member = create_cdc_member(user=create_user(username="inactive-member"), active=False)

    stdout = StringIO()
    call_command("deactivate_cdc_members", stdout=stdout)

    active_member.refresh_from_db()
    inactive_member.refresh_from_db()

    assert active_member.active is False
    assert inactive_member.active is False
    assert "Deactivated 1 Concert Donor Club members." in stdout.getvalue()


def test_deactivate_cdc_members_skips_cc_removal_without_contact_id(
    create_user,
    create_cdc_member,
    settings,
    monkeypatch,
):
    settings.DEBUG = False
    member = create_cdc_member(user=create_user(username="active-member"), active=True)
    oauth_user = create_user(username="oauth-user", email="oauth@example.com")
    OAuth2Token.objects.create(
        name="constant_contact",
        token_type="Bearer",
        access_token="access-token",
        refresh_token="refresh-token",
        expires_at=123,
        user=oauth_user,
    )

    monkeypatch.setattr(
        "concerts.signals.ConstantContactCDCListSettings.load",
        lambda: SimpleNamespace(cdc_list_id="list-123"),
    )
    monkeypatch.setattr("concerts.models.cc_get_contact_id", Mock(return_value=None))
    remove_contact = Mock()
    monkeypatch.setattr("concerts.signals.cc_remove_contact_from_cdc_list", remove_contact)

    stdout = StringIO()
    call_command("deactivate_cdc_members", stdout=stdout)

    member.refresh_from_db()

    assert member.active is False
    remove_contact.assert_not_called()
    assert "Deactivated 1 Concert Donor Club members." in stdout.getvalue()
