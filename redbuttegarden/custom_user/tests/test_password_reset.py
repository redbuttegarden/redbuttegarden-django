from django.core import mail
from django.test import Client
from django.urls import reverse

from .test_auth_access import wagtail_admin_user


def test_pasword_reset_flow(wagtail_admin_user):
    """
    Make sure users can reset their passwords
    """
    c = Client()
    response = c.post(reverse('password_reset'), {'email': wagtail_admin_user.email})
    assert len(mail.outbox) == 1
    assert  'Password reset on' in mail.outbox[0].subject
    assert response.status_code == 302


