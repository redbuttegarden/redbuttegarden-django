from datetime import datetime
import pytest

from django.contrib.auth.models import Group
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from concerts.models import Concert, ConcertDonorClubMember, Ticket, ConcertDonorClubPackage


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
def create_cdc_ticket(create_user, create_cdc_member, create_concert, create_cdc_package, user=None):
    def _create_cdc_ticket(barcode, owner=None, concert=None, package=None, user=user):
        user = user or create_user()
        owner = owner or create_cdc_member(user)
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


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    https://pytest-django.readthedocs.io/en/latest/faq.html#how-can-i-give-database-access-to-all-my-tests-without-the-django-db-marker
    """
    pass


@pytest.fixture
def create_user(django_user_model):
    def _create_user(username='cdc_test_user', first_name='first', last_name='last', email='test@email.com'):
        return django_user_model.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                                     email=email)

    return _create_user


@pytest.fixture
def create_cdc_member():
    def _create_cdc_member(user, phone='123-456-7890', packages=None, active=True):
        cdc_member = ConcertDonorClubMember(user=user, phone_number=phone, active=active)
        cdc_member.save()

        if packages:
            cdc_member.packages.add(packages)

        return cdc_member

    return _create_cdc_member


@pytest.fixture
def create_cdc_group():
    cdc_group = Group.objects.create(name='Concert Donor Club Member')

    return cdc_group


@pytest.fixture
def create_api_user_and_token(django_user_model):
    user = django_user_model.objects.create_user(username='api_user')
    token = Token.objects.create(user=user)
    return user, token


@pytest.fixture
def drf_client_with_user(create_api_user_and_token):
    user, token = create_api_user_and_token
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    return client