import os

from django.shortcuts import render


def social_media(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        facebook_api_token = os.environ.get('FB_API_TOKEN', '')
    return render(request, 'home/social_media.html',)
