import os

from django.shortcuts import render


def social_media(request):
    facebook_api_token = os.environ.get('FB_API_TOKEN', '')
    return render(request, 'home/social_media.html', {'fb_token': facebook_api_token})
