from django.shortcuts import render


def concerts(request):
    return render(request, 'concerts/concert_page.html')
