import logging

from authlib.integrations.django_client import OAuth
from django.conf import settings
from django.apps import apps

client_id = settings.CONSTANT_CONTACT_API_CLIENT_ID
logger = logging.getLogger(__name__)

def fetch_token(name, request):
    OAuth2Token = apps.get_model('concerts', 'OAuth2Token')
    try:
        token = OAuth2Token.objects.get(
            name=name,
            user=request.user
        )
    except OAuth2Token.DoesNotExist:
        return None

    return token.to_token()

oauth = OAuth(fetch_token=fetch_token)

oauth.register(
    name='constant_contact',
    client_id=client_id,
    client_secret=settings.CONSTANT_CONTACT_API_CLIENT_SECRET,
    access_token_url="https://authz.constantcontact.com/oauth2/default/v1/token",
    authorize_url="https://authz.constantcontact.com/oauth2/default/v1/authorize",
    access_token_params=None,
    authorize_params=None,
    api_base_url="https://api.cc.email/v3/",
    client_kwargs={'scope': 'account_read contact_data offline_access'},
)


def cc_add_contact_to_cdc_list(request, email_address, list_id):
    body = {
        "email_address": email_address,
        "list_memberships": [
            list_id
        ]
    }
    return oauth.constant_contact.post('https://api.cc.email/v3/contacts/sign_up_form',
                                   request=request, json=body)


def cc_get_contact_id(request, email_address):
    params = {
        "email": email_address,
    }
    response = oauth.constant_contact.get('https://api.cc.email/v3/contacts',
                                   request=request, params=params)
    logger.debug(response.json())
    return response.json()['contacts'][0]['contact_id']


def cc_remove_contact_from_cdc_list(request, concert_donor_club_member, list_id):
    body = {
        "source": {
            "contact_ids": [str(concert_donor_club_member.constant_contact_id)]
        },
        "list_ids": [
            list_id
        ]
    }

    return oauth.constant_contact.post('https://api.cc.email/v3/activities/remove_list_memberships',
                                   request=request, json=body)