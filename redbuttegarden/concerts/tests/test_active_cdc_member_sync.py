from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import requests
from django.core.management import call_command
from django.core.management.base import CommandError

from concerts.models import ConcertDonorClubMember, Ticket
from concerts.services.active_cdc_members import (
    ActiveCDCRosterSyncError,
    fetch_active_cdc_member_snapshot,
    sync_active_cdc_members_from_snapshot,
)


class DummyResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def make_snapshot(*members, generated_at="2026-04-14T12:34:56Z"):
    return {
        "snapshot_generated_at": generated_at,
        "source": "etix_active_cdc_members",
        "members": list(members),
    }


def test_fetch_active_cdc_member_snapshot_uses_token_auth(settings):
    settings.INTRANET_ACTIVE_CDC_MEMBERS_URL = "https://intranet.example.com/etix/api/active-cdc-members/"
    settings.INTRANET_ACTIVE_CDC_MEMBERS_TOKEN = "secret-token"
    settings.INTRANET_ACTIVE_CDC_MEMBERS_TIMEOUT = 9
    payload = make_snapshot(
        {
            "etix_username": "jdoe",
            "email": "jdoe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "801-555-1234",
        }
    )
    get = Mock(return_value=DummyResponse(200, payload))

    snapshot = fetch_active_cdc_member_snapshot(requests_module=SimpleNamespace(get=get))

    assert snapshot == payload
    get.assert_called_once_with(
        "https://intranet.example.com/etix/api/active-cdc-members/",
        headers={
            "Authorization": "Token secret-token",
            "Accept": "application/json",
        },
        timeout=9,
    )


@pytest.mark.parametrize("status_code", [401, 503])
def test_fetch_active_cdc_member_snapshot_raises_on_upstream_auth_or_server_failure(settings, status_code):
    settings.INTRANET_ACTIVE_CDC_MEMBERS_URL = "https://intranet.example.com/etix/api/active-cdc-members/"
    settings.INTRANET_ACTIVE_CDC_MEMBERS_TOKEN = "secret-token"

    with pytest.raises(ActiveCDCRosterSyncError):
        fetch_active_cdc_member_snapshot(
            requests_module=SimpleNamespace(
                get=Mock(return_value=DummyResponse(status_code, {"detail": "nope"}))
            )
        )


def test_fetch_active_cdc_member_snapshot_raises_on_request_exception(settings):
    settings.INTRANET_ACTIVE_CDC_MEMBERS_URL = "https://intranet.example.com/etix/api/active-cdc-members/"
    settings.INTRANET_ACTIVE_CDC_MEMBERS_TOKEN = "secret-token"

    with pytest.raises(ActiveCDCRosterSyncError):
        fetch_active_cdc_member_snapshot(
            requests_module=SimpleNamespace(
                get=Mock(side_effect=requests.RequestException("boom"))
            )
        )


def test_sync_active_cdc_members_from_snapshot_rejects_empty_snapshot_when_it_would_deactivate_active_members(
    create_user,
    create_cdc_member,
    settings,
):
    settings.DEBUG = True
    active_member = create_cdc_member(user=create_user(username="active-member"), active=True)
    inactive_member = create_cdc_member(user=create_user(username="inactive-member"), active=False)

    with pytest.raises(ActiveCDCRosterSyncError, match="Refusing to apply an empty active CDC member snapshot"):
        sync_active_cdc_members_from_snapshot(make_snapshot())

    active_member.refresh_from_db()
    inactive_member.refresh_from_db()

    assert active_member.active is True
    assert inactive_member.active is False


def test_sync_active_cdc_members_from_snapshot_allows_empty_snapshot_when_explicitly_enabled(
    create_user,
    create_cdc_member,
    settings,
):
    settings.DEBUG = True
    settings.INTRANET_ACTIVE_CDC_MEMBERS_ALLOW_EMPTY_SNAPSHOT = True
    active_member = create_cdc_member(user=create_user(username="active-member"), active=True)
    inactive_member = create_cdc_member(user=create_user(username="inactive-member"), active=False)

    result = sync_active_cdc_members_from_snapshot(make_snapshot())

    active_member.refresh_from_db()
    inactive_member.refresh_from_db()

    assert active_member.active is False
    assert inactive_member.active is False
    assert result.total_members == 0
    assert result.deactivated_members == 1


def test_sync_active_cdc_members_from_snapshot_reconciles_multiple_members(
    create_user,
    create_cdc_member,
    settings,
):
    settings.DEBUG = True
    existing_user = create_user(username="existing-member", email="old@example.com")
    existing_member = create_cdc_member(user=existing_user, active=False, phone="111-111-1111")

    result = sync_active_cdc_members_from_snapshot(
        make_snapshot(
            {
                "etix_username": "existing-member",
                "email": "existing@example.com",
                "first_name": "Existing",
                "last_name": "Member",
                "phone_number": "801-555-1111",
            },
            {
                "etix_username": "new-member",
                "email": "new@example.com",
                "first_name": "New",
                "last_name": "Member",
                "phone_number": "801-555-2222",
            },
        )
    )

    existing_member.refresh_from_db()
    existing_user.refresh_from_db()
    new_member = ConcertDonorClubMember.objects.get(user__username="new-member")

    assert existing_member.active is True
    assert existing_member.phone_number == "801-555-1111"
    assert existing_user.email == "existing@example.com"
    assert new_member.active is True
    assert new_member.phone_number == "801-555-2222"
    assert result.total_members == 2
    assert result.created_users == 1
    assert result.created_members == 1
    assert result.activated_members == 1


def test_sync_active_cdc_members_from_snapshot_keeps_zero_ticket_active_member_active(
    create_user,
    create_cdc_member,
    settings,
):
    settings.DEBUG = True
    user = create_user(username="zero-ticket-member")
    member = create_cdc_member(user=user, active=True)

    result = sync_active_cdc_members_from_snapshot(
        make_snapshot(
            {
                "etix_username": "zero-ticket-member",
                "email": "zero-ticket@example.com",
                "first_name": "Zero",
                "last_name": "Ticket",
                "phone_number": "801-555-9999",
            }
        )
    )

    member.refresh_from_db()
    user.refresh_from_db()

    assert member.active is True
    assert Ticket.objects.filter(owner=member).count() == 0
    assert user.email == "zero-ticket@example.com"
    assert result.deactivated_members == 0


def test_sync_active_cdc_members_from_snapshot_marks_removed_members_inactive(
    create_user,
    create_cdc_member,
    settings,
):
    settings.DEBUG = True
    retained_member = create_cdc_member(user=create_user(username="retained-member"), active=True)
    removed_member = create_cdc_member(user=create_user(username="removed-member"), active=True)

    result = sync_active_cdc_members_from_snapshot(
        make_snapshot(
            {
                "etix_username": "retained-member",
                "email": "retained@example.com",
                "first_name": "Retained",
                "last_name": "Member",
                "phone_number": "801-555-0001",
            }
        )
    )

    retained_member.refresh_from_db()
    removed_member.refresh_from_db()

    assert retained_member.active is True
    assert removed_member.active is False
    assert result.deactivated_members == 1


def test_sync_active_cdc_members_from_snapshot_matches_by_username_and_tolerates_nulls(
    create_user,
    create_cdc_member,
    settings,
):
    settings.DEBUG = True
    user = create_user(
        username="stable-member",
        email="before@example.com",
        first_name="Before",
        last_name="Name",
    )
    member = create_cdc_member(user=user, active=False, phone="801-555-4444")

    result = sync_active_cdc_members_from_snapshot(
        make_snapshot(
            {
                "etix_username": "stable-member",
                "email": None,
                "first_name": "After",
                "last_name": None,
                "phone_number": None,
            }
        )
    )

    user.refresh_from_db()
    member.refresh_from_db()

    assert member.active is True
    assert user.pk == member.user_id
    assert user.email == "before@example.com"
    assert user.first_name == "After"
    assert user.last_name == "Name"
    assert member.phone_number == "801-555-4444"
    assert result.activated_members == 1


def test_sync_active_cdc_members_command_raises_on_upstream_failure(monkeypatch):
    monkeypatch.setattr(
        "concerts.management.commands.sync_active_cdc_members.sync_active_cdc_members_from_intranet",
        Mock(side_effect=ActiveCDCRosterSyncError("upstream failed")),
    )

    with pytest.raises(CommandError):
        call_command("sync_active_cdc_members")


def test_sync_active_cdc_members_command_prints_summary(monkeypatch):
    monkeypatch.setattr(
        "concerts.management.commands.sync_active_cdc_members.sync_active_cdc_members_from_intranet",
        Mock(
            return_value=SimpleNamespace(
                total_members=2,
                source="etix_active_cdc_members",
                created_users=1,
                updated_users=1,
                created_members=1,
                activated_members=1,
                deactivated_members=1,
            )
        ),
    )

    stdout = StringIO()
    call_command("sync_active_cdc_members", stdout=stdout)

    output = stdout.getvalue()
    assert "Synced 2 active CDC members from etix_active_cdc_members." in output
    assert "Created users: 1, updated users: 1, created members: 1, activated members: 1, deactivated members: 1." in output
