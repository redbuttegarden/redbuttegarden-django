"""Read-only local subject snapshots for neutral external integrations."""

from __future__ import annotations

from dataclasses import dataclass

from django.contrib.auth.models import AbstractUser
from django.db.models import Count, Q
from django.utils import timezone

from concerts.models import ConcertDonorClubMember, Ticket
from memberships.models import MembershipLevel


@dataclass(frozen=True)
class LocalCDCPackageSummary:
    """Local concert package catalog data attached to a member snapshot."""

    id: int
    name: str
    year: int

    def as_external_payload(self) -> dict[str, object]:
        """Return allowlisted package fields for external integration reads."""

        return {
            "id": self.id,
            "name": self.name,
            "year": self.year,
        }


@dataclass(frozen=True)
class LocalCDCStatusSummary:
    """Local concert club status with counts only, excluding ticket secrets."""

    member_id: int
    active: bool
    packages: tuple[LocalCDCPackageSummary, ...]
    current_season_package_ticket_count: int
    current_season_additional_ticket_count: int
    current_season_ticket_count: int

    def as_external_payload(self) -> dict[str, object]:
        """Return allowlisted concert club status fields for external reads."""

        return {
            "member_id": self.member_id,
            "active": self.active,
            "packages": [
                package.as_external_payload() for package in self.packages
            ],
            "current_season_package_ticket_count": (
                self.current_season_package_ticket_count
            ),
            "current_season_additional_ticket_count": (
                self.current_season_additional_ticket_count
            ),
            "current_season_ticket_count": self.current_season_ticket_count,
        }


@dataclass(frozen=True)
class LocalMembershipLevelSummary:
    """Active local membership level catalog fields safe for integration reads."""

    id: int
    name: str
    cardholders_included: int
    admissions_allowed: int
    member_sale_ticket_allowance: int
    price: str

    def as_external_payload(self) -> dict[str, object]:
        """Return allowlisted membership level fields for external reads."""

        return {
            "id": self.id,
            "name": self.name,
            "cardholders_included": self.cardholders_included,
            "admissions_allowed": self.admissions_allowed,
            "member_sale_ticket_allowance": self.member_sale_ticket_allowance,
            "price": self.price,
        }


@dataclass(frozen=True)
class LocalIntegrationSubject:
    """Serializable local subject snapshot for a Django user."""

    id: int | None
    username: str
    first_name: str
    last_name: str
    email: str
    cdc_status: LocalCDCStatusSummary | None
    membership_levels: tuple[LocalMembershipLevelSummary, ...]

    def as_external_payload(self) -> dict[str, object]:
        """Return the explicit allowlisted payload for external integration reads."""

        cdc_status = (
            self.cdc_status.as_external_payload()
            if self.cdc_status is not None
            else None
        )
        return {
            "schema_version": 1,
            "id": self.id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "cdc_status": cdc_status,
            "membership_levels": [
                level.as_external_payload() for level in self.membership_levels
            ],
        }


def get_local_integration_subject(user: AbstractUser) -> LocalIntegrationSubject:
    """Return a read-only local integration subject snapshot for a user."""

    return LocalIntegrationSubject(
        id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        cdc_status=get_local_cdc_status_summary(user),
        membership_levels=get_active_membership_level_summaries(),
    )


def get_local_cdc_status_summary(
    user: AbstractUser,
) -> LocalCDCStatusSummary | None:
    """Return local concert club status for a user, or None when absent."""

    cdc_member = (
        ConcertDonorClubMember.objects.filter(user=user)
        .prefetch_related("packages")
        .first()
    )
    if cdc_member is None:
        return None

    current_year = timezone.localdate().year
    ticket_counts = Ticket.objects.filter(
        owner=cdc_member,
        concert__begin__year=current_year,
    ).aggregate(
        package_ticket_count=Count("id", filter=Q(package__isnull=False)),
        additional_ticket_count=Count("id", filter=Q(package__isnull=True)),
        total_ticket_count=Count("id"),
    )

    return LocalCDCStatusSummary(
        member_id=cdc_member.id,
        active=cdc_member.active,
        packages=tuple(
            LocalCDCPackageSummary(
                id=package.id,
                name=package.name,
                year=package.year,
            )
            for package in cdc_member.packages.all()
        ),
        current_season_package_ticket_count=ticket_counts["package_ticket_count"] or 0,
        current_season_additional_ticket_count=(
            ticket_counts["additional_ticket_count"] or 0
        ),
        current_season_ticket_count=ticket_counts["total_ticket_count"] or 0,
    )


def get_active_membership_level_summaries() -> tuple[LocalMembershipLevelSummary, ...]:
    """Return active local membership level catalog summaries."""

    return tuple(
        LocalMembershipLevelSummary(
            id=level.id,
            name=level.name,
            cardholders_included=level.cardholders_included,
            admissions_allowed=level.admissions_allowed,
            member_sale_ticket_allowance=level.member_sale_ticket_allowance,
            price=str(level.price),
        )
        for level in MembershipLevel.objects.filter(active=True).order_by("name").only(
            "id",
            "name",
            "cardholders_included",
            "admissions_allowed",
            "member_sale_ticket_allowance",
            "price",
        )
    )
