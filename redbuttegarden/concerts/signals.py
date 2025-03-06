import logging

from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver
from authlib.integrations.django_client import token_update
from django.http import HttpRequest

from .models import OAuth2Token, ConcertDonorClubMember, ConstantContactCDCListSettings
from .utils.constant_contact import cc_add_contact_to_cdc_list, cc_remove_contact_from_cdc_list

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


@receiver(pre_save, sender=ConcertDonorClubMember)
def update_cc_list_membership_if_changed(sender, instance, **kwargs):
    logger.debug(f'ConcertDonorClubMember pre_save signal received for instance: {instance}')
    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass
    else:
        if not obj.active == instance.active: # Field has changed
            request = HttpRequest()
            request.user = OAuth2Token.objects.filter(name='constant_contact').first().user

            if instance.active:
                list_id = ConstantContactCDCListSettings.load().cdc_list_id
                response = cc_add_contact_to_cdc_list(request, instance, list_id)
                logger.debug(f'Constant Contact response: {response.json()}')
            else:
                list_id = ConstantContactCDCListSettings.load().cdc_list_id
                response = cc_remove_contact_from_cdc_list(request, instance, list_id)
                logger.debug(f'Constant Contact response: {response.json()}')
