import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from concerts.models import Ticket, ConcertDonorClubMember, ConcertDonorClubPackage
from concerts.views import process_ticket_data, TicketDRFViewSet


def test_process_ticket_data_view_unauthorized(drf_request_factory):
    request = drf_request_factory.post(reverse('concerts:api-cdc-etix-data'), {'data': 'dummy_data'}, format='json')
    response = process_ticket_data(request)
    assert response.status_code == 401


def test_ticket_drf_viewset_unauthorized(drf_request_factory, create_cdc_ticket):
    """
    Anonymous users should not be able to view the details of a ticket from the TicketDRFViewSet
    """
    assert not Ticket.objects.all().exists()
    ticket = create_cdc_ticket(etix_id=1, concert_etix_id=1, barcode=1234567890)
    assert Ticket.objects.all().exists()
    request = drf_request_factory.get(reverse('concerts:cdc-tickets', args=[ticket.pk]))
    view = TicketDRFViewSet.as_view({'get': 'retrieve'})
    response = view(request)
    assert response.status_code == 401


def test_anonymous_user_cannot_view_cdc_ticket_detail_view(drf_request_factory, make_ticket_data, create_user):
    """
    Anonymous users should not be able to use the TicketDRFViewSet to make changes
    """
    user = create_user(username='existing-user', email='Initial')
    assert user.email == 'Initial'
    issued_ticket_data = make_ticket_data('ISSUED', etix_username='existing-user', owner_email='Updated')
    request = drf_request_factory.post(reverse('concerts:api-cdc-etix-data'), issued_ticket_data, format='json')
    view = TicketDRFViewSet.as_view({'post': 'update'})
    response = view(request)
    assert response.status_code == 401
    user.refresh_from_db()
    assert user.email == 'Initial'


def test_ticket_drf_viewset_authorized(drf_client_with_user, create_cdc_ticket):
    """
    Authorized users should be able to view the details of a ticket from the TicketDRFViewSet
    """
    assert not Ticket.objects.all().exists()
    ticket = create_cdc_ticket(barcode=1234567890, etix_id=1, concert_etix_id=1)
    assert Ticket.objects.all().exists()
    response = drf_client_with_user.get(reverse('concerts:cdc-tickets-detail', args=[ticket.pk]))
    assert response.status_code == 200


def test_ticket_drf_viewset_authorized_query_by_year(drf_client_with_user, create_user, create_cdc_member,
                                                     create_concert, create_cdc_ticket):
    """
    Authorized users should be able to filter ticket results from the TicketDRFViewSet by concert year
    """
    assert not Ticket.objects.all().exists()
    owner_user = create_user(username='ticket_owner')
    ticket_owner = create_cdc_member(user=owner_user)
    concert_2024 = create_concert(etix_id=1, year=2024)
    concert_2025 = create_concert(etix_id=2, year=2025)
    ticket_2024 = create_cdc_ticket(barcode=1234567890, etix_id=1, owner=ticket_owner, concert=concert_2024)
    ticket_2025 = create_cdc_ticket(barcode=1234567891, etix_id=2, owner=ticket_owner, concert=concert_2025)
    assert Ticket.objects.filter(concert__begin__year=2024).count() == 1
    response = drf_client_with_user.get(reverse('concerts:cdc-tickets-list') + '?year=2024', headers={'Accept': 'application/json'})
    assert response.status_code == 200
    response_json = response.json()
    assert response_json['count'] == 1
    assert response_json['results'][0]['pk'] == ticket_2024.pk


def test_ticket_drf_viewset_authorized_query_by_etix_id(drf_client_with_user, create_user, create_cdc_member,
                                                        create_cdc_ticket):
    """
    Authorized users should be able to filter ticket results from the TicketDRFViewSet by concert year
    """
    assert not Ticket.objects.all().exists()
    owner_user = create_user(username='ticket_owner')
    ticket_owner = create_cdc_member(user=owner_user)
    ticket_one = create_cdc_ticket(barcode=1234567890, owner=ticket_owner, etix_id=2234567890, concert_etix_id=1)
    ticket_two = create_cdc_ticket(barcode=1234567891, owner=ticket_owner, etix_id=2234567891, concert_etix_id=2)
    assert Ticket.objects.all().exists()
    response = drf_client_with_user.get(reverse('concerts:cdc-tickets-list') + '?etix_id=2234567890', headers={'Accept': 'application/json'}, follow=True)
    assert response.status_code == 200
    print(response)
    print(response.content)
    response_json = response.json()
    assert response_json['count'] == 1
    assert response_json['results'][0]['etix_id'] == ticket_one.etix_id


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
