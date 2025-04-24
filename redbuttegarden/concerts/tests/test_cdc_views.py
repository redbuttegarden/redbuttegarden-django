import pytest

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
    assert response.url.startswith('/accounts/login/')


def test_logged_in_user_cannot_view_cdc_portal_page(client, cdc_portal_page, create_user):
    """
    Test that a default logged in user cannot view the CDC portal Wagtail Page.
    """
    client.force_login(create_user())
    response = client.get(cdc_portal_page.get_url())
    assert response.status_code == 302  # Redirect to login page
    assert response.url.startswith('/accounts/login/')
