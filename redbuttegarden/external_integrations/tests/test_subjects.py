"""Tests for read-only local integration subject snapshots."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from django.utils import timezone

from concerts.models import (
    Concert,
    ConcertDonorClubMember,
    ConcertDonorClubPackage,
    OAuth2Token,
    Ticket,
)
from external_integrations.subjects import get_local_integration_subject
from memberships.models import MembershipLevel


pytestmark = pytest.mark.django_db


def test_subject_for_user_without_cdc_record_has_no_cdc_status(create_user) -> None:
    """A user without a local concert club row still gets a basic snapshot."""

    user = create_user(
        username="local-user",
        first_name="Local",
        last_name="User",
        email="local@example.com",
    )

    subject = get_local_integration_subject(user)

    assert subject.id == user.id
    assert subject.username == "local-user"
    assert subject.first_name == "Local"
    assert subject.last_name == "User"
    assert subject.email == "local@example.com"
    assert subject.cdc_status is None
    assert subject.as_external_payload()["cdc_status"] is None


def test_active_cdc_record_includes_packages_and_current_season_ticket_counts(
    create_user,
) -> None:
    """Active local concert club data is summarized without ticket details."""

    user = create_user(username="active-cdc")
    package = _create_package(name="Season Package", year=timezone.localdate().year)
    member = ConcertDonorClubMember.objects.create(user=user, active=True)
    member.packages.add(package)
    current_concert = _create_concert(etix_id=101, year=timezone.localdate().year)
    prior_concert = _create_concert(etix_id=102, year=timezone.localdate().year - 1)
    Ticket.objects.create(
        owner=member,
        concert=current_concert,
        package=package,
        order_id=1,
        etix_id=1,
        barcode=1111111111,
    )
    Ticket.objects.create(
        owner=member,
        concert=current_concert,
        package=None,
        order_id=2,
        etix_id=2,
        barcode=2222222222,
    )
    Ticket.objects.create(
        owner=member,
        concert=prior_concert,
        package=package,
        order_id=3,
        etix_id=3,
        barcode=3333333333,
    )

    subject = get_local_integration_subject(user)

    assert subject.cdc_status is not None
    assert subject.cdc_status.member_id == member.id
    assert subject.cdc_status.active is True
    assert subject.cdc_status.packages[0].as_external_payload() == {
        "id": package.id,
        "name": "Season Package",
        "year": timezone.localdate().year,
    }
    assert subject.cdc_status.current_season_package_ticket_count == 1
    assert subject.cdc_status.current_season_additional_ticket_count == 1
    assert subject.cdc_status.current_season_ticket_count == 2
    assert subject.cdc_status.as_external_payload() == {
        "member_id": member.id,
        "active": True,
        "packages": [
            {
                "id": package.id,
                "name": "Season Package",
                "year": timezone.localdate().year,
            }
        ],
        "current_season_package_ticket_count": 1,
        "current_season_additional_ticket_count": 1,
        "current_season_ticket_count": 2,
    }


def test_inactive_cdc_record_is_reported_without_claiming_active_status(
    create_user,
) -> None:
    """Inactive local concert club rows are represented with active=False."""

    user = create_user(username="inactive-cdc")
    member = ConcertDonorClubMember.objects.create(user=user, active=False)

    subject = get_local_integration_subject(user)

    assert subject.cdc_status is not None
    assert subject.cdc_status.member_id == member.id
    assert subject.cdc_status.active is False
    assert subject.cdc_status.current_season_ticket_count == 0


def test_subject_includes_active_membership_level_catalog_summaries(
    create_user,
) -> None:
    """Only active membership levels appear as catalog summaries."""

    active_level = _create_membership_level(
        name="Garden 2",
        cardholders=2,
        admissions=4,
        tickets=2,
        price=Decimal("95.00"),
        active=True,
    )
    _create_membership_level(
        name="Retired",
        cardholders=1,
        admissions=1,
        tickets=0,
        price=Decimal("40.00"),
        active=False,
    )
    user = create_user(username="membership-catalog")

    subject = get_local_integration_subject(user)

    assert subject.as_external_payload() == {
        "schema_version": 1,
        "id": user.id,
        "username": "membership-catalog",
        "first_name": "",
        "last_name": "",
        "email": "",
        "cdc_status": None,
        "membership_levels": [
            {
                "id": active_level.id,
                "name": "Garden 2",
                "cardholders_included": 2,
                "admissions_allowed": 4,
                "member_sale_ticket_allowance": 2,
                "price": "95.00",
            }
        ],
    }
    assert subject.membership_levels[0].as_external_payload() == {
        "id": active_level.id,
        "name": "Garden 2",
        "cardholders_included": 2,
        "admissions_allowed": 4,
        "member_sale_ticket_allowance": 2,
        "price": "95.00",
    }


def test_subject_external_payload_excludes_sensitive_local_integration_fields(
    create_user,
) -> None:
    """External payload serialization excludes local secrets and identifiers."""

    user = create_user(username="sensitive-user")
    package = _create_package(name="Sensitive Package", year=timezone.localdate().year)
    provider_contact_id = uuid4()
    member = ConcertDonorClubMember.objects.create(
        user=user,
        active=True,
        constant_contact_id=provider_contact_id,
        chat_access_token="chat-secret-token",
    )
    member.packages.add(package)
    Ticket.objects.create(
        owner=member,
        concert=_create_concert(etix_id=888201, year=timezone.localdate().year),
        package=package,
        order_id=777004,
        etix_id=777204,
        barcode=444444444444,
    )
    OAuth2Token.objects.create(
        name="local-token",
        token_type="Bearer",
        access_token="oauth-access-secret",
        refresh_token="oauth-refresh-secret",
        expires_at=9999999999,
        user=user,
    )

    payload = get_local_integration_subject(user).as_external_payload()
    payload_text = repr(payload)

    assert set(payload) == {
        "schema_version",
        "id",
        "username",
        "first_name",
        "last_name",
        "email",
        "cdc_status",
        "membership_levels",
    }
    assert "chat_access_token" not in payload_text
    assert "chat-secret-token" not in payload_text
    assert "constant_contact_id" not in payload_text
    assert str(provider_contact_id) not in payload_text
    assert "order_id" not in payload_text
    assert "777004" not in payload_text
    assert "etix_id" not in payload_text
    assert "777204" not in payload_text
    assert "888201" not in payload_text
    assert "444444444444" not in payload_text
    assert "barcode" not in payload_text
    assert "oauth-access-secret" not in payload_text
    assert "oauth-refresh-secret" not in payload_text
    assert "access_token" not in payload_text
    assert "refresh_token" not in payload_text


def _create_concert(*, etix_id: int, year: int) -> Concert:
    """Create a local concert row for snapshot tests."""

    begin = timezone.make_aware(datetime(year=year, month=6, day=1, hour=19))
    end = timezone.make_aware(datetime(year=year, month=6, day=1, hour=21))
    return Concert.objects.create(
        etix_id=etix_id,
        name=f"Concert {etix_id}",
        begin=begin,
        end=end,
    )


def _create_package(*, name: str, year: int) -> ConcertDonorClubPackage:
    """Create a local concert package row for snapshot tests."""

    return ConcertDonorClubPackage.objects.create(name=name, year=year)


def _create_membership_level(
    *,
    name: str,
    cardholders: int,
    admissions: int,
    tickets: int,
    price: Decimal,
    active: bool,
) -> MembershipLevel:
    """Create a local membership level row for snapshot tests."""

    return MembershipLevel.objects.create(
        name=name,
        cardholders_included=cardholders,
        admissions_allowed=admissions,
        member_sale_ticket_allowance=tickets,
        price=price,
        active=active,
    )
