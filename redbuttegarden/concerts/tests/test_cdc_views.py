import html
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.contrib.auth.models import Group
from django.template.loader import render_to_string
from django.urls import reverse

from wagtail.models import Page, PageViewRestriction

from concerts.models import ConcertDonorClubPortalPage
from concerts.services.image_probe import ImageProbeResult


@pytest.fixture
def cdc_portal_page(admin_user, create_cdc_group):
    """
    Pytest fixture to create a ConcertDonorClubPortalPage with a page
    view restriction that restricts viewing to members of the group
    returned by the create_cdc_group fixture.
    """
    home = Page.objects.get(slug='home')
    portal_page = ConcertDonorClubPortalPage(owner=admin_user, title="CDC Portal", slug="concert-club-portal")
    home.add_child(instance=portal_page)
    portal_page.save_revision().publish()
    restriction = PageViewRestriction.objects.create(page=portal_page, restriction_type='groups')
    restriction.groups.set([create_cdc_group])

    return portal_page


def test_anonymous_user_cannot_view_cdc_portal_page(client, cdc_portal_page):
    """
    Test that an anonymous user cannot view the CDC portal Wagtail Page.
    """
    response = client.get(cdc_portal_page.get_url())
    assert response.status_code == 302  # Redirect to login page
    assert response.url.startswith('/accounts/login')


def test_anonymous_user_cannot_view_cdc_concert_detail_tickets_page(client, create_cdc_ticket, create_concert):
    """
    Test that an anonymous user cannot view ticket details for a
    particular concert returned by concert_detail_tickets_view.
    """
    ticket = create_cdc_ticket(etix_id=1, concert_etix_id=1, barcode='1234567890')
    response = client.get(reverse('concerts:cdc-tickets', args=[ticket.concert.pk]))
    assert response.status_code == 302  # Redirect to login page
    assert response.url.startswith('/accounts/login')


def test_logged_in_user_cannot_view_cdc_portal_page(client, cdc_portal_page, create_user):
    """
    Test that a default logged in user cannot view the CDC portal Wagtail Page.
    """
    client.force_login(create_user())
    response = client.get(cdc_portal_page.get_url())
    assert response.status_code == 302  # Redirect to login page
    assert response.url.startswith('/accounts/login/')


def test_logged_in_active_cdc_member_wrong_group_cannot_view_cdc_portal_page(client, cdc_portal_page, create_user,
                                                                             create_cdc_member):
    """
    Test that a logged in active CDC member cannot view the CDC portal
    Wagtail Page if they are not also in the Concert Donor Club Member
    Group.
    """
    cdc_user = create_user()
    cdc_member = create_cdc_member(user=cdc_user)
    client.force_login(cdc_user)
    assert cdc_member.active
    assert cdc_user.groups.filter(name='Concert Donor Club Member').exists() is False
    response = client.get(cdc_portal_page.get_url())
    assert response.status_code == 302  # Redirect to login page
    assert response.url.startswith('/accounts/login')


def test_logged_in_active_cdc_member_correct_group_can_view_cdc_portal_page(client, cdc_portal_page, create_user,
                                                                            create_cdc_member, settings):
    """
    Test that a logged in active CDC member can view the CDC portal
    Wagtail Page if they are also in the Concert Donor Club Member
    Group.
    """
    settings.CONCERTS_CDC_PROFILE_ENABLED = True
    cdc_user = create_user()
    cdc_group = Group.objects.get(name='Concert Donor Club Member')
    cdc_user.groups.add(cdc_group)
    cdc_member = create_cdc_member(user=cdc_user)
    client.force_login(cdc_user)
    assert cdc_member.active
    assert cdc_user.groups.filter(name='Concert Donor Club Member').exists() is True
    response = client.get(cdc_portal_page.get_url())
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    assert 'CDC Portal' in content
    assert reverse('concerts:cdc-profile') in content


def test_logged_in_inactive_cdc_member_correct_group_cannot_view_cdc_portal_page_content(client, cdc_portal_page, create_user,
                                                                             create_cdc_member):
    """
    Test that a logged in inactive CDC member can view the CDC portal
    Wagtail Page but the body content should be replaced with a message
    warning their membership is inactive.
    """
    cdc_user = create_user()
    cdc_group = Group.objects.get(name='Concert Donor Club Member')
    cdc_user.groups.add(cdc_group)
    cdc_member = create_cdc_member(user=cdc_user, active=False)
    client.force_login(cdc_user)
    assert cdc_member.active is False
    assert cdc_user.groups.filter(name='Concert Donor Club Member').exists() is True
    response = client.get(cdc_portal_page.get_url())
    assert response.status_code == 200
    assert 'your Concert Donor Club membership isn\'t currently active' in response.content.decode('utf-8')


def test_active_cdc_member_profile_view_returns_404_when_temporarily_disabled(client, create_user, create_cdc_member,
                                                                              settings):
    """
    Test that the profile view is unreachable when the temporary feature
    flag is disabled.
    """
    settings.CONCERTS_CDC_PROFILE_ENABLED = False
    cdc_user = create_user()
    cdc_member = create_cdc_member(user=cdc_user)
    client.force_login(cdc_user)

    assert cdc_member.active is True

    response = client.get(reverse('concerts:cdc-profile'))
    assert response.status_code == 404


def test_active_cdc_member_portal_hides_profile_link_when_temporarily_disabled(client, cdc_portal_page, create_user,
                                                                               create_cdc_member, settings):
    """
    Test that the portal page does not render the profile link when the
    temporary feature flag is disabled.
    """
    settings.CONCERTS_CDC_PROFILE_ENABLED = False
    cdc_user = create_user()
    cdc_group = Group.objects.get(name='Concert Donor Club Member')
    cdc_user.groups.add(cdc_group)
    cdc_member = create_cdc_member(user=cdc_user)
    client.force_login(cdc_user)

    assert cdc_member.active is True

    response = client.get(cdc_portal_page.get_url())
    content = response.content.decode('utf-8')

    assert response.status_code == 200
    assert reverse('concerts:cdc-profile') not in content
    assert 'Summer Concert Lineup' not in content


def test_check_image_url_returns_placeholder_for_invalid_input(client) -> None:
    """Invalid query parameters fail closed without starting a network probe."""

    with patch("concerts.views.probe_public_image_url") as probe:
        response = client.get(
            reverse("concerts:check-img"),
            {"image_url": "http://", "concert_name": "Concert"},
        )

    assert response.status_code == 200
    assert b'class="placeholder w-100 h-100"' in response.content
    assert b'aria-hidden="true"' in response.content
    assert b"<img" not in response.content
    probe.assert_not_called()


def test_check_image_url_requires_explicit_http_scheme(client) -> None:
    """A hostname without an explicit safe scheme does not start a probe."""

    with patch("concerts.views.probe_public_image_url") as probe:
        response = client.get(
            reverse("concerts:check-img"),
            {"image_url": "example.com/image.jpg", "concert_name": "Concert"},
        )

    assert response.status_code == 200
    assert b'class="placeholder w-100 h-100"' in response.content
    probe.assert_not_called()


def test_check_image_url_returns_placeholder_when_probe_fails(client) -> None:
    """A rejected or unavailable resource still gives HTMX swappable markup."""

    with patch("concerts.views.probe_public_image_url", return_value=None):
        response = client.get(
            reverse("concerts:check-img"),
            {"image_url": "https://example.com/image.jpg", "concert_name": "Concert"},
        )

    assert response.status_code == 200
    assert b'class="placeholder w-100 h-100"' in response.content


def test_check_image_url_escapes_final_url_and_concert_name(client) -> None:
    """The successful image fragment autoescapes all reflected values."""

    final_url = 'https://cdn.example.com/image.jpg?label="onerror=alert(1)'
    concert_name = '"><script>alert(1)</script>'
    with patch(
        "concerts.views.probe_public_image_url",
        return_value=ImageProbeResult(final_url=final_url),
    ):
        response = client.get(
            reverse("concerts:check-img"),
            {"image_url": "https://example.com/image.jpg", "concert_name": concert_name},
        )

    content = response.content.decode()
    assert response.status_code == 200
    assert 'src="https://cdn.example.com/image.jpg?label=&quot;onerror=alert(1)"' in content
    assert 'referrerpolicy="no-referrer"' in content
    assert "<script>" not in content
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in content


def test_check_image_url_uses_accessible_fallback_for_blank_concert_name(client) -> None:
    """A missing optional concert name still produces meaningful alt text."""

    with patch(
        "concerts.views.probe_public_image_url",
        return_value=ImageProbeResult(final_url="https://example.com/image.jpg"),
    ):
        response = client.get(
            reverse("concerts:check-img"),
            {"image_url": "https://example.com/image.jpg", "concert_name": ""},
        )

    assert response.status_code == 200
    assert b'alt="Concert promo art for this concert"' in response.content


def test_ticket_card_url_encodes_htmx_query_parameters() -> None:
    """Reserved characters cannot add parameters to the HTMX image request."""

    ticket = SimpleNamespace(
        image_url="https://example.com/image.jpg?existing=1&injected=2",
        name="Band & Guests = Great",
        begin="7:00 PM",
        doors="6:00 PM",
        ticket_count=2,
    )
    content = html.unescape(
        render_to_string(
            "concerts/includes/cdc_concert_ticket_cards.html",
            {
                "id": "test",
                "count": 1,
                "button_text": "Tickets",
                "tickets_dict": {"ticket": ticket},
            },
        )
    )

    assert (
        'hx-get="/concerts/api/check-img/?image_url=https%3A%2F%2Fexample.com%2Fimage.jpg%3Fexisting%3D1%26injected%3D2'
        '&concert_name=Band%20%26%20Guests%20%3D%20Great"'
    ) in content
