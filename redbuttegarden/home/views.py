from django.shortcuts import render


def social_media(request):
    return render(request, 'home/social_media.html')
