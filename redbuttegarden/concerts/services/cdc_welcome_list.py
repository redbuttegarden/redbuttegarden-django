import logging
from dataclasses import dataclass
from datetime import timedelta

from django.db import models
from django.http import HttpRequest
from django.utils import timezone

from concerts.models import (
    ConcertDonorClubMember,
    ConcertDonorClubWelcomeListAdd,
    ConstantContactCDCListSettings,
    OAuth2Token,
)
from concerts.utils.constant_contact import (
    cc_add_contact_to_cdc_list,
    cc_contact_has_list_membership,
    cc_get_contact_by_email,
)

logger = logging.getLogger(__name__)


class CDCWelcomeListError(Exception):
    pass


@dataclass
class CDCWelcomeListQueueResult:
    list_id: str
    total_active_members: int = 0
    queued: int = 0
    existing: int = 0
    skipped: int = 0
    dry_run: bool = False


@dataclass
class CDCWelcomeListProcessResult:
    list_id: str
    considered: int = 0
    processed: int = 0
    added: int = 0
    already_member: int = 0
    skipped: int = 0
    failed: int = 0
    dry_run: bool = False


def queue_active_cdc_members_for_welcome_list(
    list_id=None,
    source=ConcertDonorClubWelcomeListAdd.Source.MANUAL,
    dry_run=False,
):
    list_id = list_id or get_configured_cdc_list_id()
    result = CDCWelcomeListQueueResult(list_id=list_id, dry_run=dry_run)
    active_members = ConcertDonorClubMember.objects.filter(active=True).select_related("user")
    logger.info(
        "Starting CDC welcome list queue: list_id=%s source=%s dry_run=%s",
        list_id,
        source,
        dry_run,
    )

    for member in active_members.iterator():
        result.total_active_members += 1
        if not _member_has_email(member):
            result.skipped += 1
            logger.warning(
                "Skipping CDC welcome list queue because member has no email: %s list_id=%s dry_run=%s",
                _member_log_context(member),
                list_id,
                dry_run,
            )
            continue

        if dry_run:
            exists = ConcertDonorClubWelcomeListAdd.objects.filter(
                member=member,
                list_id=list_id,
            ).exists()
            if exists:
                result.existing += 1
                logger.info(
                    "CDC welcome list queue row already exists: %s list_id=%s dry_run=%s",
                    _member_log_context(member),
                    list_id,
                    dry_run,
                )
                continue

            result.queued += 1
            logger.info(
                "Would queue CDC welcome list row: %s list_id=%s source=%s",
                _member_log_context(member),
                list_id,
                source,
            )
        else:
            entry, created = ConcertDonorClubWelcomeListAdd.objects.get_or_create(
                member=member,
                list_id=list_id,
                defaults={"source": source},
            )
            if created:
                result.queued += 1
                logger.info(
                    "Queued CDC welcome list row: entry_id=%s %s list_id=%s source=%s",
                    entry.pk,
                    _member_log_context(member),
                    list_id,
                    source,
                )
            else:
                result.existing += 1
                logger.info(
                    "CDC welcome list queue row already exists: entry_id=%s %s list_id=%s",
                    entry.pk,
                    _member_log_context(member),
                    list_id,
                )

    logger.info(
        "Completed CDC welcome list queue: list_id=%s dry_run=%s active_checked=%s queued=%s existing=%s skipped=%s",
        result.list_id,
        result.dry_run,
        result.total_active_members,
        result.queued,
        result.existing,
        result.skipped,
    )
    return result


def process_cdc_welcome_list_adds(
    list_id=None,
    limit=25,
    dry_run=False,
    stale_processing_minutes=60,
):
    list_id = list_id or get_configured_cdc_list_id()
    result = CDCWelcomeListProcessResult(list_id=list_id, dry_run=dry_run)
    entries = _processable_entries(list_id, stale_processing_minutes)
    logger.info(
        "Starting CDC welcome list processing: list_id=%s limit=%s dry_run=%s stale_processing_minutes=%s",
        list_id,
        limit,
        dry_run,
        stale_processing_minutes,
    )

    if limit is not None:
        entries = entries[:limit]
    entries = list(entries)

    request = None if dry_run or not entries else _get_constant_contact_request()
    for entry in entries:
        result.considered += 1
        if dry_run:
            logger.info(
                "Would process CDC welcome list row: entry_id=%s status=%s %s list_id=%s",
                entry.pk,
                entry.status,
                _member_log_context(entry.member),
                entry.list_id,
            )
            continue
        if not _claim_entry(entry, stale_processing_minutes):
            logger.info(
                "Skipping CDC welcome list row because it was already claimed: entry_id=%s status=%s %s list_id=%s",
                entry.pk,
                entry.status,
                _member_log_context(entry.member),
                entry.list_id,
            )
            continue
        _process_entry(entry, request, result)

    logger.info(
        "Completed CDC welcome list processing: list_id=%s dry_run=%s considered=%s processed=%s added=%s already_member=%s skipped=%s failed=%s",
        result.list_id,
        result.dry_run,
        result.considered,
        result.processed,
        result.added,
        result.already_member,
        result.skipped,
        result.failed,
    )
    return result


def get_configured_cdc_list_id():
    list_id = getattr(ConstantContactCDCListSettings.load(), "cdc_list_id", None)
    if not list_id:
        raise CDCWelcomeListError("Constant Contact CDC list id is not configured.")
    return list_id


def _processable_entries(list_id, stale_processing_minutes):
    stale_before = timezone.now() - timedelta(minutes=stale_processing_minutes)
    return (
        ConcertDonorClubWelcomeListAdd.objects.filter(list_id=list_id)
        .filter(
            models.Q(
                status__in=[
                    ConcertDonorClubWelcomeListAdd.Status.PENDING,
                    ConcertDonorClubWelcomeListAdd.Status.FAILED,
                ]
            )
            | models.Q(
                status=ConcertDonorClubWelcomeListAdd.Status.PROCESSING,
                attempted_at__lt=stale_before,
            )
        )
        .select_related("member", "member__user")
        .order_by("created_at", "pk")
    )


def _claim_entry(entry, stale_processing_minutes):
    stale_before = timezone.now() - timedelta(minutes=stale_processing_minutes)
    claimed = ConcertDonorClubWelcomeListAdd.objects.filter(pk=entry.pk).filter(
        models.Q(
            status__in=[
                ConcertDonorClubWelcomeListAdd.Status.PENDING,
                ConcertDonorClubWelcomeListAdd.Status.FAILED,
            ]
        )
        | models.Q(
            status=ConcertDonorClubWelcomeListAdd.Status.PROCESSING,
            attempted_at__lt=stale_before,
        )
    ).update(
        status=ConcertDonorClubWelcomeListAdd.Status.PROCESSING,
        attempted_at=timezone.now(),
        last_error="",
    )
    if claimed:
        entry.refresh_from_db()
        logger.info(
            "Claimed CDC welcome list row for processing: entry_id=%s status=%s %s list_id=%s",
            entry.pk,
            entry.status,
            _member_log_context(entry.member),
            entry.list_id,
        )
    return bool(claimed)


def _process_entry(entry, request, result):
    member = entry.member
    if not member.active:
        result.skipped += 1
        entry.status = ConcertDonorClubWelcomeListAdd.Status.PENDING
        entry.save(update_fields=["status", "updated_at"])
        logger.info(
            "Deferred CDC welcome list row because member is inactive: entry_id=%s %s list_id=%s",
            entry.pk,
            _member_log_context(member),
            entry.list_id,
        )
        return

    if not _member_has_email(member):
        _mark_skipped(entry, "CDC member does not have an email address.")
        result.skipped += 1
        logger.warning(
            "Skipped CDC welcome list row because member has no email: entry_id=%s %s list_id=%s",
            entry.pk,
            _member_log_context(member),
            entry.list_id,
        )
        return

    try:
        logger.info(
            "Checking Constant Contact membership for CDC welcome list row: entry_id=%s %s list_id=%s",
            entry.pk,
            _member_log_context(member),
            entry.list_id,
        )
        contact = cc_get_contact_by_email(request, member.user.email)
        if contact:
            contact_id = contact.get("contact_id")
            logger.info(
                "Found Constant Contact contact for CDC member: entry_id=%s contact_id=%s %s list_id=%s",
                entry.pk,
                contact_id,
                _member_log_context(member),
                entry.list_id,
            )
            _store_contact_id(entry, member, contact_id)
            if cc_contact_has_list_membership(contact, entry.list_id):
                entry.status = ConcertDonorClubWelcomeListAdd.Status.ALREADY_MEMBER
                entry.added_at = timezone.now()
                entry.save(update_fields=["status", "contact_id", "added_at", "updated_at"])
                result.already_member += 1
                result.processed += 1
                logger.info(
                    "CDC member is already on Constant Contact welcome list; no add call made: entry_id=%s contact_id=%s %s list_id=%s",
                    entry.pk,
                    contact_id,
                    _member_log_context(member),
                    entry.list_id,
                )
                return
        else:
            logger.info(
                "No Constant Contact contact found for CDC member before welcome list add: entry_id=%s %s list_id=%s",
                entry.pk,
                _member_log_context(member),
                entry.list_id,
            )

        logger.info(
            "Adding CDC member to Constant Contact welcome list: entry_id=%s %s list_id=%s",
            entry.pk,
            _member_log_context(member),
            entry.list_id,
        )
        response = cc_add_contact_to_cdc_list(request, member, entry.list_id)
        if not response.ok:
            response_text = getattr(response, "text", "")
            _mark_failed(entry, f"Constant Contact returned {response.status_code}: {response_text}")
            result.failed += 1
            result.processed += 1
            logger.warning(
                "Failed to add CDC member to Constant Contact welcome list: entry_id=%s status_code=%s response=%s %s list_id=%s",
                entry.pk,
                response.status_code,
                response_text,
                _member_log_context(member),
                entry.list_id,
            )
            return

        payload = response.json()
        _store_contact_id(entry, member, payload.get("contact_id"))
        entry.status = ConcertDonorClubWelcomeListAdd.Status.ADDED
        entry.added_at = timezone.now()
        entry.save(update_fields=["status", "contact_id", "added_at", "updated_at"])
        result.added += 1
        result.processed += 1
        logger.info(
            "Added CDC member to Constant Contact welcome list: entry_id=%s contact_id=%s %s list_id=%s",
            entry.pk,
            payload.get("contact_id"),
            _member_log_context(member),
            entry.list_id,
        )
    except Exception as exc:
        logger.exception(
            "Unable to add CDC member to Constant Contact welcome list: entry_id=%s %s list_id=%s",
            entry.pk,
            _member_log_context(member),
            entry.list_id,
        )
        _mark_failed(entry, str(exc))
        result.failed += 1
        result.processed += 1


def _get_constant_contact_request():
    oauth_token = OAuth2Token.objects.filter(name="constant_contact").select_related("user").first()
    if oauth_token is None:
        raise CDCWelcomeListError("No Constant Contact OAuth token is configured.")

    logger.info(
        "Using Constant Contact OAuth token for CDC welcome list processing: token_id=%s user_id=%s username=%s",
        oauth_token.pk,
        oauth_token.user_id,
        oauth_token.user.username,
    )
    request = HttpRequest()
    request.user = oauth_token.user
    return request


def _member_has_email(member):
    return bool(member.user_id and member.user and member.user.email)


def _store_contact_id(entry, member, contact_id):
    if not contact_id:
        return

    entry.contact_id = contact_id
    if str(member.constant_contact_id or "") != str(contact_id):
        member.constant_contact_id = contact_id
        member.save(update_fields=["constant_contact_id"])
        logger.info(
            "Stored Constant Contact contact id on CDC member: contact_id=%s %s",
            contact_id,
            _member_log_context(member),
        )


def _mark_failed(entry, message):
    entry.status = ConcertDonorClubWelcomeListAdd.Status.FAILED
    entry.last_error = message
    entry.save(update_fields=["status", "last_error", "updated_at"])
    logger.warning(
        "Marked CDC welcome list row failed: entry_id=%s error=%s %s list_id=%s",
        entry.pk,
        message,
        _member_log_context(entry.member),
        entry.list_id,
    )


def _mark_skipped(entry, message):
    entry.status = ConcertDonorClubWelcomeListAdd.Status.SKIPPED
    entry.last_error = message
    entry.save(update_fields=["status", "last_error", "updated_at"])
    logger.info(
        "Marked CDC welcome list row skipped: entry_id=%s reason=%s %s list_id=%s",
        entry.pk,
        message,
        _member_log_context(entry.member),
        entry.list_id,
    )


def _member_log_context(member):
    username = getattr(member.user, "username", None) if member.user_id else None
    email = getattr(member.user, "email", None) if member.user_id else None
    return f"member_id={member.pk} user_id={member.user_id} username={username!r} email={email!r}"
