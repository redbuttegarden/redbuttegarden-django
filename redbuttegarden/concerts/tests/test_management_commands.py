from io import StringIO

from django.core.management import call_command

from concerts.models import ConcertDonorClubWelcomeListAdd


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


def test_deactivate_cdc_members_does_not_queue_welcome_list_changes(
    create_user,
    create_cdc_member,
    settings,
):
    settings.DEBUG = False
    member = create_cdc_member(user=create_user(username="active-member"), active=True)

    stdout = StringIO()
    call_command("deactivate_cdc_members", stdout=stdout)

    member.refresh_from_db()

    assert member.active is False
    assert ConcertDonorClubWelcomeListAdd.objects.count() == 0
    assert "Deactivated 1 Concert Donor Club members." in stdout.getvalue()
