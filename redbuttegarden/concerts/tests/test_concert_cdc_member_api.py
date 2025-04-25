import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from concerts.models import ConcertDonorClubMember


@pytest.fixture
def make_cdc_member_data():
    def _make_cdc_member_data(username="johndoe", first_name="John", last_name="Doe", title="Test CDC Member",
                              email="test@email.com"):
        return {
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "title": title,
            "email": email
        }

    return _make_cdc_member_data


def test_get_list_concert_donor_club_member_drf_viewset_unauthorized():
    """
    Unauthorized requests to ConcertDonorClubMemberDRFViewSet list view
    should return 401 status code.
    """
    client = APIClient()
    response = client.get(reverse('concerts:cdc-members-list'))
    assert response.status_code == 401


def test_get_list_concert_donor_club_member_drf_viewset_authorized(drf_client_with_user, create_user, create_cdc_member):
    """
    Authorized requests to ConcertDonorClubMemberDRFViewSet list view
    should return list of ConcertDonorClubMember objects.
    """
    response = drf_client_with_user.get(reverse('concerts:cdc-members-list'))
    assert response.status_code == 200
    assert response.json()['count'] == 0  # Assuming no members exist in the database

    cdc_user = create_user()
    create_cdc_member(user=cdc_user)
    response = drf_client_with_user.get(reverse('concerts:cdc-members-list'))
    assert response.status_code == 200
    assert response.json()['count'] == 1  # Assuming one member was created


def test_get_detail_concert_donor_club_member_drf_viewset_unauthorized():
    """
    Unauthorized requests to ConcertDonorClubMemberDRFViewSet detail view
    should return 401 status code.
    """
    client = APIClient()
    response = client.get(reverse('concerts:cdc-members-detail', args=[1]))
    assert response.status_code == 401
