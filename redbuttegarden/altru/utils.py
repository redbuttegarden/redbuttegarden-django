from altru.models import AltruAccessToken


def token_saver(token):
    # Save the Token to the database
    AltruAccessToken.objects.create(token=token)
