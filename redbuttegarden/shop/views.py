from django.shortcuts import render
from django.urls import reverse
from rest_framework.decorators import api_view
from rest_framework.exceptions import bad_request
from rest_framework.response import Response

from shop.utils import check_snipcart_token_valid


@api_view(['POST'])
def payment_methods(request):
    """
    Return available payment methods to Snipcart
    """
    # Validate request is from Snipcart servers
    if not check_snipcart_token_valid(request):
        return bad_request

    return Response([
        {
            'id': 'snipcart_custom_gateway_1',
            'name': 'Payconex',
            'checkoutUrl': reverse('shop-checkout'),
        }
    ])

def checkout(request):
    return render(request, 'shop/checkout.html')

@api_view(['POST'])
def snipcart_webhook(request):
    # TODO - webhook logic
    pass