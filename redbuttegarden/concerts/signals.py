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
    if settings.DEBUG:
        logger.debug("Skipping Constant Contact CDC sync in DEBUG mode.")
        return

    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    if obj.active == instance.active:
        return

    oauth_token = OAuth2Token.objects.filter(name='constant_contact').first()
    if oauth_token is None:
        logger.warning(
            "Skipping Constant Contact CDC sync for %s because no OAuth token is configured.",
            instance,
        )
        return

    list_id = getattr(ConstantContactCDCListSettings.load(), "cdc_list_id", None)
    if not list_id:
        logger.warning(
            "Skipping Constant Contact CDC sync for %s because no CDC list id is configured.",
            instance,
        )
        return

    if not instance.active and not instance.constant_contact_id:
        logger.warning(
            "Skipping Constant Contact CDC removal for %s because no Constant Contact contact id is configured.",
            instance,
        )
        return

    request = HttpRequest()
    request.user = oauth_token.user

    if instance.active:
        response = cc_add_contact_to_cdc_list(request, instance, list_id)
    else:
        response = cc_remove_contact_from_cdc_list(request, instance, list_id)

    logger.debug(f'Constant Contact response: {response.json()}')
