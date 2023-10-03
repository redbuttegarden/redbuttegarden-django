import requests

def check_snipcart_token_valid(request):
    """
    Check the given request for a valid Snipcart token.

    Return True if valid.
    """
    snipcart_public_token = request.GET.get('publicToken', '')

    if not snipcart_public_token:
        return False

    response = requests.get(
        f'https://payment.snipcart.com/api/public/custom-payment-gateway/validate?publicToken={snipcart_public_token}')

    if response.ok:
        return True
    else:
        return False
