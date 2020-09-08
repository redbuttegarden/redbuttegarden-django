from django.http import Http404
from django.shortcuts import render


def about_us(request):
    return render(request, 'home/about-us.html')


def directions(request):
    return render(request, 'home/directions.html')


def general_info(request):
    return render(request, 'home/general-info.html')
