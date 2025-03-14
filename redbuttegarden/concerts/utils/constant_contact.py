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


def cc_add_contact_to_cdc_list(request, concert_donor_club_member, list_id):
    """
    Adds CC contact to CDC list and updates their account with CDC member details

    Endpoint reference:
    https://developer.constantcontact.com/api_reference/index.html#tag/Contacts/operation/createOrUpdateContact
    """
    body = {
        "first_name": str(concert_donor_club_member.user.first_name),
        "last_name": str(concert_donor_club_member.user.last_name),
        "email_address": str(concert_donor_club_member.user.email),
        "phone_number": str(concert_donor_club_member.phone_number),
        "custom_fields": [
            {
                # UUID for custom field "CDC Username" in Constant Contact
                "custom_field_id": "98fec5e4-fabd-11ef-ab8a-fa163eeb983a",
                "value": str(concert_donor_club_member.user.username)
            }
        ],
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
    try:
        contact_id = response.json()['contacts'][0]['contact_id']
    except IndexError as e:
        # Likely that the contact does not exist in CC
        logger.warning(f'Error getting CC ID when searching with {email_address}.\nError: {e}')
        return None

    return contact_id


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