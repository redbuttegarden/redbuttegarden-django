import json

from django.db import models


class AltruAccessToken(models.Model):
    id = models.BigAutoField(primary_key=True)
    token = models.JSONField()

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        get_latest_by = 'updated'

    def __str__(self):
        return json.dumps(self.token)
