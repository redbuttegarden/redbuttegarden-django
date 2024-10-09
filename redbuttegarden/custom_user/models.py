from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    title = models.CharField(max_length=255)

    class Meta:
        ordering = ['last_name', 'first_name', 'username']

    def __repr__(self):
        return f'{self.first_name} {self.last_name} ({self.username})'

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.username})'
