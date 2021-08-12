import logging

from django.shortcuts import render, redirect

logger = logging.getLogger(__name__)

def concerts(request):
    return render(request, 'concerts/concert_page.html')

def concert_thank_you(request):
    referer = request.META.get('HTTP_REFERER')
    logger.debug(f'Referer: {referer}')
    logger.debug(f'HTTP META Dictionary: {request.META}')
    if referer and 'etix.com' in referer:
        return render(request, 'concerts/concert_thank_you.html')
    else:
        return redirect('/')
