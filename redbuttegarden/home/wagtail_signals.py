import os

from wagtail.core.signals import page_published
import requests


# Send POST request to Microsoft Automate
def send_to_automate(sender, **kwargs):
    instance = kwargs['instance']
    url = os.environ.get('AUTOMATE_URL')
    values = {
        "text" : "%s was published by %s " % (instance.title, instance.owner.username),
    }

    response = requests.post(url, values)


page_published.connect(send_to_automate)
