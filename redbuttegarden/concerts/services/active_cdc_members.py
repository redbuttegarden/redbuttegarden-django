import logging
from dataclasses import dataclass

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from concerts.models import ConcertDonorClubMember

logger = logging.getLogger(__name__)

CDC_MEMBER_GROUP_NAME = "Concert Donor Club Member"
ACTIVE_CDC_MEMBER_SOURCE = "etix_active_cdc_members"


class ActiveCDCRosterSyncError(Exception):
    pass


@dataclass(frozen=True)
class ActiveCDCRosterMember:
    etix_username: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None


@dataclass
class ActiveCDCRosterSyncResult:
    snapshot_generated_at: str | None
    source: str | None
    total_members: int
    created_users: int = 0
    updated_users: int = 0
    created_members: int = 0
    updated_members: int = 0
    activated_members: int = 0
    deactivated_members: int = 0


def fetch_active_cdc_member_snapshot(requests_module=requests):
    url = getattr(settings, "INTRANET_ACTIVE_CDC_MEMBERS_URL", None)
    token = getattr(settings, "INTRANET_ACTIVE_CDC_MEMBERS_TOKEN", None)
    timeout = getattr(settings, "INTRANET_ACTIVE_CDC_MEMBERS_TIMEOUT", 10)

    if not url:
        raise ActiveCDCRosterSyncError("INTRANET_ACTIVE_CDC_MEMBERS_URL is not configured.")
    if not token:
        raise ActiveCDCRosterSyncError("INTRANET_ACTIVE_CDC_MEMBERS_TOKEN is not configured.")

    try:
        response = requests_module.get(
            url,
            headers={
                "Authorization": f"Token {token}",
                "Accept": "application/json",
            },
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise ActiveCDCRosterSyncError(
            f"Unable to fetch active CDC member snapshot: {exc}"
        ) from exc

    if response.status_code != 200:
        raise ActiveCDCRosterSyncError(
            f"Unable to fetch active CDC member snapshot: upstream returned {response.status_code}."
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise ActiveCDCRosterSyncError(
            "Unable to fetch active CDC member snapshot: upstream returned invalid JSON."
        ) from exc

    if not isinstance(payload, dict):
        raise ActiveCDCRosterSyncError("Active CDC member snapshot payload must be a JSON object.")

    return payload


def sync_active_cdc_members_from_intranet(requests_module=requests):
    snapshot = fetch_active_cdc_member_snapshot(requests_module=requests_module)
    return sync_active_cdc_members_from_snapshot(snapshot)


def sync_active_cdc_members_from_snapshot(snapshot):
    normalized_members = _normalize_snapshot(snapshot)
    _validate_snapshot_safety(normalized_members)
    result = ActiveCDCRosterSyncResult(
        snapshot_generated_at=snapshot.get("snapshot_generated_at"),
        source=snapshot.get("source"),
        total_members=len(normalized_members),
    )
    usernames_in_snapshot = [member.etix_username for member in normalized_members]

    logger.info(
        "Syncing %s active CDC members from %s snapshot generated at %s.",
        len(normalized_members),
        result.source or "unknown source",
        result.snapshot_generated_at or "unknown time",
    )

    cdc_group, _ = Group.objects.get_or_create(name=CDC_MEMBER_GROUP_NAME)
    user_model = get_user_model()

    for member_payload in normalized_members:
        user_defaults = _build_user_defaults(member_payload)
        user, user_created = user_model.objects.get_or_create(
            username=member_payload.etix_username,
            defaults=user_defaults,
        )
        if user_created:
            result.created_users += 1
        else:
            user_updated = False
            for field_name, value in user_defaults.items():
                if getattr(user, field_name) != value:
                    setattr(user, field_name, value)
                    user_updated = True
            if user_updated:
                user.save(update_fields=list(user_defaults.keys()))
                result.updated_users += 1

        user.groups.add(cdc_group)

        member_defaults = {"active": True}
        if member_payload.phone_number is not None:
            member_defaults["phone_number"] = member_payload.phone_number

        cdc_member, member_created = ConcertDonorClubMember.objects.get_or_create(
            user=user,
            defaults=member_defaults,
        )
        if member_created:
            result.created_members += 1
            continue

        update_fields = []
        if not cdc_member.active:
            cdc_member.active = True
            update_fields.append("active")
            result.activated_members += 1
        if (
            member_payload.phone_number is not None
            and cdc_member.phone_number != member_payload.phone_number
        ):
            cdc_member.phone_number = member_payload.phone_number
            update_fields.append("phone_number")
        if update_fields:
            cdc_member.save(update_fields=update_fields)
            result.updated_members += 1

    members_to_deactivate = ConcertDonorClubMember.objects.filter(active=True)
    if usernames_in_snapshot:
        members_to_deactivate = members_to_deactivate.exclude(
            user__username__in=usernames_in_snapshot
        )

    for cdc_member in members_to_deactivate.iterator():
        cdc_member.active = False
        cdc_member.save(update_fields=["active"])
        result.deactivated_members += 1

    logger.info(
        "Completed active CDC roster sync: %s created users, %s updated users, %s created members, %s activated members, %s deactivated members.",
        result.created_users,
        result.updated_users,
        result.created_members,
        result.activated_members,
        result.deactivated_members,
    )
    return result


def _validate_snapshot_safety(normalized_members):
    if normalized_members:
        return

    active_member_count = ConcertDonorClubMember.objects.filter(active=True).count()
    if active_member_count == 0:
        return

    if getattr(settings, "INTRANET_ACTIVE_CDC_MEMBERS_ALLOW_EMPTY_SNAPSHOT", False):
        return

    raise ActiveCDCRosterSyncError(
        "Refusing to apply an empty active CDC member snapshot while "
        f"{active_member_count} local CDC members are still active. "
        "Set INTRANET_ACTIVE_CDC_MEMBERS_ALLOW_EMPTY_SNAPSHOT=true to allow this intentionally."
    )


def _normalize_snapshot(snapshot):
    members = snapshot.get("members")
    if not isinstance(members, list):
        raise ActiveCDCRosterSyncError("Active CDC member snapshot must include a members list.")

    normalized_members = []
    seen_usernames = set()

    for index, raw_member in enumerate(members):
        if not isinstance(raw_member, dict):
            raise ActiveCDCRosterSyncError(
                f"Active CDC member snapshot entry {index} is not an object."
            )

        username = raw_member.get("etix_username")
        if not isinstance(username, str) or not username.strip():
            raise ActiveCDCRosterSyncError(
                f"Active CDC member snapshot entry {index} is missing a valid etix_username."
            )

        normalized_username = username.strip()
        if normalized_username in seen_usernames:
            raise ActiveCDCRosterSyncError(
                f"Active CDC member snapshot contains duplicate etix_username {normalized_username!r}."
            )
        seen_usernames.add(normalized_username)

        normalized_members.append(
            ActiveCDCRosterMember(
                etix_username=normalized_username,
                email=_normalize_optional_string(raw_member.get("email")),
                first_name=_normalize_optional_string(raw_member.get("first_name")),
                last_name=_normalize_optional_string(raw_member.get("last_name")),
                phone_number=_normalize_optional_string(raw_member.get("phone_number")),
            )
        )

    return sorted(normalized_members, key=lambda member: member.etix_username)


def _build_user_defaults(member_payload):
    user_defaults = {}
    for field_name in ("email", "first_name", "last_name"):
        value = getattr(member_payload, field_name)
        if value is not None:
            user_defaults[field_name] = value
    return user_defaults


def _normalize_optional_string(value):
    if value is None:
        return None
    return str(value)
