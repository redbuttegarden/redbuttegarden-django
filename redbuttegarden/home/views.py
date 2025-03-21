import os

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render

from home.models import CurrentWeather


def social_media(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        facebook_api_token = os.environ.get('FB_API_TOKEN', '')
    return render(request, 'home/social_media.html',)


def latest_weather(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        weather = CurrentWeather.objects.first()
        if weather:
            return JsonResponse({
                'condition': weather.condition,
                'temperature': weather.temperature,
            })

    return HttpResponse(status=204)
