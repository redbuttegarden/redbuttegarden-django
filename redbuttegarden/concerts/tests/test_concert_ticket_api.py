import json

import pytest
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory, APIClient

from concerts.models import Ticket, ConcertDonorClubMember, ConcertDonorClubPackage
from concerts.views import process_ticket_data


@pytest.mark.django_db
@pytest.fixture
def create_api_user_and_token(django_user_model):
    user = django_user_model.objects.create_user(username='api_user')
    token = Token.objects.create(user=user)
    return user, token


@pytest.mark.django_db
@pytest.fixture
def create_cdc_package():
    cdc_package = ConcertDonorClubPackage(name='Test Package', year=2024)
    cdc_package.save()

    return cdc_package


@pytest.fixture
def create_user(django_user_model):
    def _create_user(username='cdc_test_user'):
        return django_user_model.objects.create_user(username=username)

    return _create_user


@pytest.fixture
def create_cdc_member():
    def _create_cdc_member(user, phone='123-456-7890', packages=None):
        cdc_member = ConcertDonorClubMember(user=user, phone_number=phone)
        cdc_member.save()

        if packages:
            cdc_member.packages.add(packages)

        return cdc_member

    return _create_cdc_member


@pytest.fixture
def drf_request_factory():
    return APIRequestFactory()


@pytest.fixture
def drf_client_with_user(create_api_user_and_token):
    user, token = create_api_user_and_token
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    return client


@pytest.fixture
def make_ticket_data():
    def _make_ticket_data(ticket_status, etix_username='test-user'):
        return {
            "order_id": 99999999,
            "etix_username": etix_username,
            "package_name": "Opener Placeholder",
            "event_name": "Markéta Irglová and Glen Hansard of The Swell Season",
            "event_id": 12934887,
            "event_begin": "2024-01-30T19:31:45.261Z",
            "event_end": "2024-01-30T19:31:45.261Z",
            "event_doors_before_event_time_minutes": 60,
            "event_image_url": "https://event.etix.com/ticket/json/files/get?file=1477ca2a-f33a-47a6-bdec-827df3edc859&alt=150w",
            "ticket_status": ticket_status,
            "ticket_barcode": "11546743321"
        }

    return _make_ticket_data


def test_process_ticket_data_view_unauthorized(drf_request_factory):
    request = drf_request_factory.post(reverse('concerts:api-cdc-etix-data'), {'data': 'dummy_data'}, format='json')
    response = process_ticket_data(request)
    assert response.status_code == 401


@pytest.mark.django_db
def test_process_ticket_data_view_no_cdc_member(create_api_user_and_token, drf_client_with_user, make_ticket_data):
    issued_ticket_data = make_ticket_data('ISSUED')
    response = drf_client_with_user.post(reverse('concerts:api-cdc-etix-data'), issued_ticket_data, format='json')
    assert response.status_code == 200
    assert json.loads(response.content.decode())['status'] == 'No matching CDC member found.'
    with pytest.raises(Ticket.DoesNotExist):
        Ticket.objects.get(barcode=issued_ticket_data['ticket_barcode'])


@pytest.mark.django_db
def test_process_ticket_data_view_issued(create_user, create_cdc_member, create_api_user_and_token,
                                         drf_client_with_user, make_ticket_data):
    cdc_user = create_user()
    create_cdc_member(user=cdc_user)
    issued_ticket_data = make_ticket_data(ticket_status='ISSUED', etix_username=cdc_user.username)
    drf_client_with_user.post(reverse('concerts:api-cdc-etix-data'), issued_ticket_data, format='json')
    assert Ticket.objects.filter(barcode=issued_ticket_data['ticket_barcode']).exists()
