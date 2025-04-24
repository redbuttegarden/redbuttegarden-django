import pytest

from django.contrib.auth.models import Group


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
def create_cdc_group():
    cdc_group = Group.objects.create(name='Concert Donor Club Member')

    return cdc_group
