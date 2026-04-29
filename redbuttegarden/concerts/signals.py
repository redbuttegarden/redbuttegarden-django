import logging

from django.dispatch import receiver
from authlib.integrations.django_client import token_update

from .models import OAuth2Token

logger = logging.getLogger(__name__)


@receiver(token_update)
def on_token_update(sender, name, token, refresh_token=None, access_token=None, **kwargs):
    if refresh_token:
        try:
            item = OAuth2Token.objects.get(name=name, refresh_token=refresh_token)
        except OAuth2Token.DoesNotExist:
            return
    elif access_token:
        try:
            item = OAuth2Token.objects.get(name=name, access_token=access_token)
        except OAuth2Token.DoesNotExist:
            return
    else:
        return

    # update old token
    item.access_token = token['access_token']
    item.refresh_token = token.get('refresh_token')
    item.expires_at = token['expires_at']
    item.save()
