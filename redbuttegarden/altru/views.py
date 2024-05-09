from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from requests_oauthlib import OAuth2Session

from .models import AltruAccessToken

from altru.utils import token_saver


@login_required(login_url='/admin')
def altru_auth(request):
    """Step 1: User Authorization.

    Redirect the user/resource owner to the OAuth provider (i.e. Blackbaud)
    using a URL with a few key OAuth parameters.
    """
    client_id = settings.ALTRU_API_CLIENT_ID

    redirect_uri = request.build_absolute_uri(reverse('altru:api-callback'))
    blackbaud = OAuth2Session(client_id, redirect_uri=redirect_uri)
    authorization_url, state = blackbaud.authorization_url(settings.ALTRU_AUTHORIZATION_BASE_URL,
                                                           # offline for refresh token
                                                           # force to always make user click authorize
                                                           access_type="offline", prompt="select_account")

    # State is used to prevent CSRF, keep this for later.
    request.session['oauth_state'] = state
    return redirect(authorization_url)


# Step 2: User authorization, this happens on the provider.
def callback(request):
    """ Step 3: Retrieving an access token.

    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    """
    redirect_uri = request.build_absolute_uri(reverse('altru:api-callback'))
    response_uri = request.build_absolute_uri()
    blackbaud = OAuth2Session(settings.ALTRU_API_CLIENT_ID,
                              redirect_uri=redirect_uri,
                              state=request.session['oauth_state'])
    token = blackbaud.fetch_token(settings.ALTRU_TOKEN_URL, client_secret=settings.ALTRU_API_CLIENT_SECRET,
                                  authorization_response=response_uri)

    token_saver(token)

    return redirect(reverse('altru:constituent_notes'))


@login_required(login_url='/admin')
def create_constituent_notes(request):
    if request.method == 'POST':
        data = {
            'constituent_id': '69ac75ad-3f42-4e3c-a1ca-949752f1edd5',
            'context_type': 0,
            'title': 'Notes API Test',
            'date_entered': '2023-12-19',
            'author_id': '69ac75ad-3f42-4e3c-a1ca-949752f1edd5',
            'note_type': 'Note',
            'text_note': 'Testing 123',
        }
        try:
            altru_token = AltruAccessToken.objects.filter(token__family_name=request.user.last_name).latest()
        except AltruAccessToken.DoesNotExist:
            return JsonResponse('No token found.')

        blackbaud = OAuth2Session(settings.ALTRU_API_CLIENT_ID, token=altru_token.token,
                                  auto_refresh_url=settings.ALTRU_TOKEN_URL,
                                  token_updater=token_saver)
        response = blackbaud.post(f'{settings.ALTRU_API_BASE}/alt-conmg/constituentnotes',
                                  headers={'Bb-Api-Subscription-Key': settings.ALTRU_API_SUBSCRIPTION_KEY,
                                           'REDatabaseToUse': settings.ALTRU_DATABASE_NAME},
                                  json=data).json()
        return JsonResponse(response)
    return render(request, 'altru/create_constituent_notes.html')
