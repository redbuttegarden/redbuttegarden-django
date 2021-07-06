from django.contrib.auth.models import AbstractUser, Group
from django.db import models


class User(AbstractUser):
    title = models.CharField(max_length=255)

    def __repr__(self):
        return f'{self.first_name} {self.last_name} ({self.username})'

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.username})'


class PlantAPIGroup(models.Model):
    name = models.CharField(verbose_name="Group", max_length=255)
    description = models.TextField(verbose_name="Description", blank=True, null=True)
    roles = models.ManyToManyField(Group, verbose_name="Role", related_name="apigroups", blank=True)

class Meta:
    verbose_name = "BRAHMS API group"
    verbose_name_plural = "BRAHMS API groups"
