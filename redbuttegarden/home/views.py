from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def social_media(request):
    return render(request, 'home/social_media.html')

@login_required
def vr_tours(request):
    return render(request, 'home/vr_tours.html')
