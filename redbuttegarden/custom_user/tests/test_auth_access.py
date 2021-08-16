import pytest

from django.contrib.auth import get_user_model, get_user
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse


@pytest.fixture
def wagtail_admin_user(db):
    user = get_user_model().objects.create_user(username='user', email='test@email.com', password='password')
    user.user_permissions.add(Permission.objects.get(codename='access_admin'))
    return user

@pytest.fixture
def normal_user(db):
    user = get_user_model().objects.create_user(username='user', email='test@email.com', password='password')
    return user


def test_wagtail_admin_wagtail_login(wagtail_admin_user):
    """
    Users with access to the Wagtail admin should not be allowed to login with views that don't implement 2FA
    """
    c = Client()
    # This post should fail to log the user in
    response = c.post(reverse('custom_user:login'), {'username': wagtail_admin_user.username, 'password': 'password'})
    assert response.status_code == 200
    assert b'RBG staff are not permitted to use this login form' in response.content

    user = get_user(c)
    assert user.is_authenticated is False

    # Attempt to access page that requires admin access
    response = c.get('/admin/')
    assert response.status_code == 302  # Should redirect to login page

    # This login attempt should succeed
    response = c.post('/admin/login/', {'username': wagtail_admin_user.username, 'password': 'password'})
    assert response.status_code == 302

    user = get_user(c)
    assert user.is_authenticated is True

    response = c.get('/admin/')
    assert response.status_code == 200  # Should load without redirection

def test_normal_user_wagtail_login(normal_user):
    """
    Users without access to the Wagtail admin can login but still can't access Wagtail admin
    """
    c = Client()
    # Login will succeed but still shouldn't be able to view wagtail admin pages
    c.post('/admin/login/', {'username': normal_user.username, 'password': 'password'})

    # Attempt to access page that requires admin access
    response = c.get('/admin/')
    assert response.status_code == 302  # Should redirect to login page

def test_logout_view(normal_user):
    """
    Authenticated users should be able to logout by visiting /accounts/logout/
    """
    c = Client()
    c.force_login(normal_user)

    user = get_user(c)
    assert user.is_authenticated is True

    response = c.get('/accounts/logout/')
    assert response.status_code == 200

    user = get_user(c)
    assert user.is_authenticated is False
