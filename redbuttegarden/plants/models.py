from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import DecimalField, CharField, ForeignKey, PositiveSmallIntegerField, DateField, DateTimeField
from django.utils.dates import MONTHS


class Family(models.Model):
    name = CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['-name']

class Genus(models.Model):
    family = ForeignKey(Family, on_delete=models.CASCADE)
    name = CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['-name']

class Species(models.Model):
    genus = ForeignKey(Genus, on_delete=models.CASCADE)
    name = CharField(max_length=255, unique=True)
    cultivar = CharField(max_length=255)
    vernacular_name = CharField(max_length=255)
    habit = CharField(max_length=255)
    hardiness = ArrayField(base_field=PositiveSmallIntegerField(validators=[MinValueValidator(1),
                                                                            MaxValueValidator(13)]),
                           size=13)
    water_regime = CharField(max_length=255)
    exposure = CharField(max_length=255)
    bloom_time = ArrayField(base_field=CharField(choices=MONTHS.items(), max_length=255))
    plant_size = CharField(max_length=255)

class Location(models.Model):
    latitude = DecimalField(max_digits=9, decimal_places=6)
    longitude = DecimalField(max_digits=9, decimal_places=6)

class Collection(models.Model):
    location = models.OneToOneField(Location, on_delete=models.CASCADE)
    species = ForeignKey(Species, on_delete=models.CASCADE)
    plant_date = DateField()
    planter = CharField(max_length=255, blank=True, null=True)  # Name of person who planted the collection
    created_on = DateTimeField(auto_now_add=True)
    last_modified = DateTimeField(auto_now=True)