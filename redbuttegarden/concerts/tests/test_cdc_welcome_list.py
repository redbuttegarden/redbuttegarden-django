from unittest.mock import Mock

from concerts.models import ConcertDonorClubWelcomeListAdd, OAuth2Token
from concerts.services.cdc_welcome_list import (
    process_cdc_welcome_list_adds,
    queue_active_cdc_members_for_welcome_list,
)


CONTACT_ID = "3b0cc288-0c0f-4cc7-8c40-632f2ecce393"


class DummyResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    @property
    def ok(self):
        return 200 <= self.status_code < 300

    def json(self):
        return self._payload


def test_queue_active_cdc_members_for_welcome_list_is_idempotent(create_user, create_cdc_member):
    active_member = create_cdc_member(
        user=create_user(username="active-member", email="active@example.com"),
        active=True,
    )
    create_cdc_member(
        user=create_user(username="active-no-email", email=""),
        active=True,
    )
    create_cdc_member(
        user=create_user(username="inactive-member", email="inactive@example.com"),
        active=False,
    )

    result = queue_active_cdc_members_for_welcome_list(list_id="list-123")
    repeat_result = queue_active_cdc_members_for_welcome_list(list_id="list-123")

    assert result.total_active_members == 2
    assert result.queued == 1
    assert result.skipped == 1
    assert repeat_result.queued == 0
    assert repeat_result.existing == 1
    assert ConcertDonorClubWelcomeListAdd.objects.filter(
        member=active_member,
        list_id="list-123",
    ).count() == 1


def test_process_cdc_welcome_list_adds_marks_existing_list_members_without_readding(
    create_user,
    create_cdc_member,
    monkeypatch,
):
    member = create_cdc_member(user=create_user(username="existing", email="existing@example.com"))
    ConcertDonorClubWelcomeListAdd.objects.create(member=member, list_id="list-123")
    _create_oauth_token(create_user)
    add_contact = Mock()
    monkeypatch.setattr(
        "concerts.services.cdc_welcome_list.cc_get_contact_by_email",
        Mock(return_value={"contact_id": CONTACT_ID, "list_memberships": ["list-123"]}),
    )
    monkeypatch.setattr(
        "concerts.services.cdc_welcome_list.cc_add_contact_to_cdc_list",
        add_contact,
    )

    result = process_cdc_welcome_list_adds(list_id="list-123")

    entry = ConcertDonorClubWelcomeListAdd.objects.get(member=member, list_id="list-123")
    member.refresh_from_db()
    assert result.already_member == 1
    assert result.added == 0
    assert entry.status == ConcertDonorClubWelcomeListAdd.Status.ALREADY_MEMBER
    assert str(member.constant_contact_id) == CONTACT_ID
    add_contact.assert_not_called()


def test_process_cdc_welcome_list_adds_adds_missing_contact_once(
    create_user,
    create_cdc_member,
    monkeypatch,
):
    member = create_cdc_member(user=create_user(username="new", email="new@example.com"))
    ConcertDonorClubWelcomeListAdd.objects.create(member=member, list_id="list-123")
    _create_oauth_token(create_user)
    add_contact = Mock(return_value=DummyResponse(payload={"contact_id": CONTACT_ID}))
    monkeypatch.setattr(
        "concerts.services.cdc_welcome_list.cc_get_contact_by_email",
        Mock(return_value=None),
    )
    monkeypatch.setattr(
        "concerts.services.cdc_welcome_list.cc_add_contact_to_cdc_list",
        add_contact,
    )

    result = process_cdc_welcome_list_adds(list_id="list-123")
    repeat_result = process_cdc_welcome_list_adds(list_id="list-123")

    entry = ConcertDonorClubWelcomeListAdd.objects.get(member=member, list_id="list-123")
    member.refresh_from_db()
    assert result.added == 1
    assert repeat_result.considered == 0
    assert entry.status == ConcertDonorClubWelcomeListAdd.Status.ADDED
    assert str(member.constant_contact_id) == CONTACT_ID
    add_contact.assert_called_once()


def test_process_cdc_welcome_list_adds_with_no_rows_does_not_require_oauth_token():
    result = process_cdc_welcome_list_adds(list_id="list-123")

    assert result.considered == 0
    assert result.processed == 0


def _create_oauth_token(create_user):
    return OAuth2Token.objects.create(
        name="constant_contact",
        token_type="Bearer",
        access_token="access-token",
        refresh_token="refresh-token",
        expires_at=123,
        user=create_user(username="oauth-user", email="oauth@example.com"),
    )
