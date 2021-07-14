from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import DecimalField, CharField, ForeignKey, PositiveSmallIntegerField, DateField, DateTimeField
from django.utils.dates import MONTHS
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel
from wagtail.core.models import Orderable
from wagtail.images.edit_handlers import ImageChooserPanel


class Family(models.Model):
    name = CharField(max_length=255, unique=True)

    def __repr__(self):
        return ' '.join([self.name])

    class Meta:
        ordering = ['name']

class Genus(models.Model):
    family = ForeignKey(Family, on_delete=models.CASCADE)
    name = CharField(max_length=255, unique=True)

    def __str__(self):
        return ' '.join([self.name, f'({self.family.name})'])

    class Meta:
        ordering = ['name']

class Species(ClusterableModel):
    genus = ForeignKey(Genus, on_delete=models.CASCADE)
    name = CharField(max_length=255, blank=True, null=True)
    cultivar = CharField(max_length=255, blank=True, null=True)
    vernacular_name = CharField(max_length=255)
    habit = CharField(max_length=255)
    hardiness = ArrayField(base_field=PositiveSmallIntegerField(validators=[MinValueValidator(1),
                                                                            MaxValueValidator(13)]),
                           size=13, blank=True, null=True)
    water_regime = CharField(max_length=255, blank=True, null=True)
    exposure = CharField(max_length=255, blank=True, null=True)
    bloom_time = ArrayField(base_field=CharField(choices=MONTHS.items(), max_length=255), blank=True, null=True)
    plant_size = CharField(max_length=255, blank=True, null=True)

    panels = [
        InlinePanel('species_images', label='Species Images'),
        FieldPanel('genus'),
        FieldPanel('name'),
        FieldPanel('cultivar'),
        FieldPanel('vernacular_name'),
        FieldPanel('habit'),
        FieldPanel('hardiness'),
        FieldPanel('water_regime'),
        FieldPanel('exposure'),
        FieldPanel('bloom_time'),
        FieldPanel('plant_size'),
    ]

    def __str__(self):
        return ' '.join([self.genus.name, self.name])

    class Meta:
        ordering = ['name']
        unique_together = ['genus', 'name', 'cultivar']
        verbose_name_plural = 'species'

class SpeciesImage(Orderable):
    species = ParentalKey(Species, on_delete=models.CASCADE, related_name='species_images')
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+'
    )
    caption = models.CharField(blank=True, max_length=250)

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('caption'),
    ]

class Location(models.Model):
    latitude = DecimalField(max_digits=9, decimal_places=6)
    longitude = DecimalField(max_digits=9, decimal_places=6)

    def __str__(self):
        return ' '.join([str(self.latitude), str(self.longitude)])

class Collection(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    species = ForeignKey(Species, on_delete=models.CASCADE)
    plant_date = DateField(blank=True, null=True)
    created_on = DateTimeField(auto_now_add=True)
    last_modified = DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_on']
