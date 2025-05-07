from datetime import datetime

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from concerts.models import Concert, Ticket, ConcertDonorClubMember, ConcertDonorClubPackage
from concerts.views import process_ticket_data, TicketDRFViewSet


@pytest.fixture
def create_concert():
    def _create_concert():
        naive_begin = datetime(year=2025, month=1, day=1, hour=19, minute=0)
        naive_end = datetime(year=2025, month=1, day=1, hour=21, minute=0)
        begin = timezone.make_aware(naive_begin, timezone.get_default_timezone())
        end = timezone.make_aware(naive_end, timezone.get_default_timezone())
        concert = Concert(
            etix_id=123456,
            name='Test Concert',
            begin=begin,
            end=end,
            doors_before_event_time_minutes=60,
            image_url='https://example.com/image.jpg',
        )
        concert.save()

        return concert

    return _create_concert


@pytest.fixture
def create_cdc_member(create_user):
    def _create_cdc_member(user=None):
        user = user or create_user()
        cdc_member = ConcertDonorClubMember(
            user=user,
            phone_number='123-456-7890',
        )
        cdc_member.save()

        return cdc_member

    return _create_cdc_member


@pytest.fixture
def create_cdc_ticket(create_cdc_member, create_concert, create_cdc_package):
    def _create_cdc_ticket(barcode, owner=None, concert=None, package=None):
        owner = owner or create_cdc_member()
        concert = concert or create_concert()
        package = package or create_cdc_package()
        cdc_ticket = Ticket(
            owner=owner,
            concert=concert,
            package=package,
            order_id=123456789,
            barcode=barcode,
        )
        cdc_ticket.save()

        return cdc_ticket

    return _create_cdc_ticket


@pytest.fixture
def create_cdc_package():
    def _create_cdc_package(name='Test Package'):
        cdc_package = ConcertDonorClubPackage(name=name, year=2024)
        cdc_package.save()

        return cdc_package

    return _create_cdc_package


@pytest.fixture
def drf_request_factory():
    return APIRequestFactory()


@pytest.fixture
def make_ticket_data():
    def _make_ticket_data(ticket_status, etix_username='test-user', owner_first_name='First', owner_last_name='Last',
                          owner_email='email@email.com', package_name='Opener Placeholder'):
        return {
            "order_id": 99999999,
            "etix_username": etix_username,
            "owner_email": owner_email,
            "owner_first_name": owner_first_name,
            "owner_last_name": owner_last_name,
            "owner_phone": "123 4569999",
            "package_name": package_name,
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


def test_ticket_drf_viewset_unauthorized(drf_request_factory, create_cdc_ticket):
    """
    Anonymous users should not be able to view the details of a ticket from the TicketDRFViewSet
    """
    assert not Ticket.objects.all().exists()
    ticket = create_cdc_ticket(barcode=1234567890)
    assert Ticket.objects.all().exists()
    request = drf_request_factory.get(reverse('concerts:cdc-tickets', args=[ticket.pk]))
    view = TicketDRFViewSet.as_view({'get': 'retrieve'})
    response = view(request)
    assert response.status_code == 401


def test_process_ticket_data_view_no_cdc_member(create_cdc_group, create_api_user_and_token, drf_client_with_user,
                                                make_ticket_data):
    """If no ConcertDonorClubMember exists, one should be created"""
    issued_ticket_data = make_ticket_data('ISSUED')
    with pytest.raises(get_user_model().DoesNotExist):
        get_user_model().objects.get(username=issued_ticket_data['etix_username'])
    with pytest.raises(ConcertDonorClubMember.DoesNotExist):
        ConcertDonorClubMember.objects.get(user__username=issued_ticket_data['etix_username'])
    response = drf_client_with_user.post(reverse('concerts:api-cdc-etix-data'), issued_ticket_data, format='json')
    assert response.status_code == 200
    assert Ticket.objects.filter(barcode=issued_ticket_data['ticket_barcode']).exists()
    assert get_user_model().objects.filter(username=issued_ticket_data['etix_username']).exists()
    assert ConcertDonorClubMember.objects.filter(user__username=issued_ticket_data['etix_username']).exists()


def test_process_ticket_data_view_no_cdc_member_first_name_asterisk(create_cdc_group, create_api_user_and_token,
                                                                    drf_client_with_user,
                                                                    make_ticket_data):
    """
    Ensure ConcertDonorClubMember can be created with a blank first
    name if the incoming owner_first_name is set to an asterisk
    """
    issued_ticket_data = make_ticket_data('ISSUED', owner_first_name='*')
    drf_client_with_user.post(reverse('concerts:api-cdc-etix-data'), issued_ticket_data, format='json')
    assert get_user_model().objects.filter(username=issued_ticket_data['etix_username']).exists()
    cdc_member = ConcertDonorClubMember.objects.get(user__username=issued_ticket_data['etix_username'])
    assert cdc_member.user.first_name == ''


def test_process_ticket_data_view_issued(create_user, create_cdc_member, create_api_user_and_token,
                                         drf_client_with_user, make_ticket_data):
    cdc_user = create_user()
    create_cdc_member(user=cdc_user)
    issued_ticket_data = make_ticket_data(ticket_status='ISSUED', etix_username=cdc_user.username)
    drf_client_with_user.post(reverse('concerts:api-cdc-etix-data'), issued_ticket_data, format='json')
    assert Ticket.objects.filter(barcode=issued_ticket_data['ticket_barcode']).exists()


def test_process_ticket_data_view_blank_package_name(create_user, create_cdc_member, create_api_user_and_token,
                                                     drf_client_with_user, make_ticket_data):
    """
    ConcertDonorClubPackages should not be created with empty string names
    """
    cdc_user = create_user()
    create_cdc_member(user=cdc_user)
    issued_ticket_data = make_ticket_data(ticket_status='ISSUED', etix_username=cdc_user.username, package_name=' ')
    drf_client_with_user.post(reverse('concerts:api-cdc-etix-data'), issued_ticket_data, format='json')
    assert Ticket.objects.filter(barcode=issued_ticket_data['ticket_barcode']).exists()
    assert not ConcertDonorClubPackage.objects.filter(name=' ').exists()


def test_process_ticket_data_view_package_name_missing(create_user, create_cdc_member, create_api_user_and_token,
                                                       drf_client_with_user, make_ticket_data):
    """
    API view should gracefully handle missing package names and ConcertDonorClubPackages should not be created
    """
    cdc_user = create_user()
    create_cdc_member(user=cdc_user)
    original_package_count = ConcertDonorClubPackage.objects.count()
    issued_ticket_data = make_ticket_data(ticket_status='ISSUED', etix_username=cdc_user.username, package_name=None)
    response = drf_client_with_user.post(reverse('concerts:api-cdc-etix-data'), issued_ticket_data, format='json',
                                         follow=True)
    assert response.status_code == 200
    assert Ticket.objects.filter(barcode=issued_ticket_data['ticket_barcode']).exists()
    assert not ConcertDonorClubPackage.objects.filter(name=None).exists()
    assert ConcertDonorClubPackage.objects.count() == original_package_count


def test_process_ticket_data_updates_user_first_name(create_cdc_group, create_api_user_and_token,
                                                     drf_client_with_user,
                                                     make_ticket_data, create_user):
    """
    Incoming ticket data should update existing users first name.
    """
    user = create_user(username='existing-user', first_name='Initial')
    assert user.first_name == 'Initial'
    issued_ticket_data = make_ticket_data('ISSUED', etix_username='existing-user', owner_first_name='Updated')
    drf_client_with_user.post(reverse('concerts:api-cdc-etix-data'), issued_ticket_data, format='json')
    user.refresh_from_db()
    assert user.first_name == 'Updated'


def test_process_ticket_data_updates_user_last_name(create_cdc_group, create_api_user_and_token,
                                                    drf_client_with_user,
                                                    make_ticket_data, create_user):
    """
    Incoming ticket data should update existing users last name.
    """
    user = create_user(username='existing-user', last_name='Initial')
    assert user.last_name == 'Initial'
    issued_ticket_data = make_ticket_data('ISSUED', etix_username='existing-user', owner_last_name='Updated')
    drf_client_with_user.post(reverse('concerts:api-cdc-etix-data'), issued_ticket_data, format='json')
    user.refresh_from_db()
    assert user.last_name == 'Updated'


def test_process_ticket_data_updates_user_email(create_cdc_group, create_api_user_and_token,
                                                drf_client_with_user,
                                                make_ticket_data, create_user):
    """
    Incoming ticket data should update existing users email.
    """
    user = create_user(username='existing-user', email='Initial')
    assert user.email == 'Initial'
    issued_ticket_data = make_ticket_data('ISSUED', etix_username='existing-user', owner_email='Updated')
    drf_client_with_user.post(reverse('concerts:api-cdc-etix-data'), issued_ticket_data, format='json')
    user.refresh_from_db()
    assert user.email == 'Updated'


def test_anonymous_user_cannot_view_cdc_ticket_detail_view(create_cdc_group, create_api_user_and_token,
                                                           drf_client_with_user,
                                                           make_ticket_data, create_user):

    user = create_user(username='existing-user', email='Initial')
    assert user.email == 'Initial'
    issued_ticket_data = make_ticket_data('ISSUED', etix_username='existing-user', owner_email='Updated')
    drf_client_with_user.post(reverse('concerts:api-cdc-etix-data'), issued_ticket_data, format='json')
    user.refresh_from_db()
    assert user.email == 'Updated'
