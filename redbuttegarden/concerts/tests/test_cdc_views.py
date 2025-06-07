import pytest
from django.contrib.auth.models import Group
from django.urls import reverse

from wagtail.models import Page, PageViewRestriction

from concerts.models import ConcertDonorClubPortalPage


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
                                                                            create_cdc_member):
    """
    Test that a logged in active CDC member can view the CDC portal
    Wagtail Page if they are also in the Concert Donor Club Member
    Group.
    """
    cdc_user = create_user()
    cdc_group = Group.objects.get(name='Concert Donor Club Member')
    cdc_user.groups.add(cdc_group)
    cdc_member = create_cdc_member(user=cdc_user)
    client.force_login(cdc_user)
    assert cdc_member.active
    assert cdc_user.groups.filter(name='Concert Donor Club Member').exists() is True
    response = client.get(cdc_portal_page.get_url())
    assert response.status_code == 200
    assert 'CDC Portal' in response.content.decode('utf-8')


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
