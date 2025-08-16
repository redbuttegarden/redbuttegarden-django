import urllib.parse

from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models.functions import Length
from django.utils.dates import MONTHS
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import InlinePanel
from wagtail.admin.panels import FieldPanel
from wagtail.models import Orderable

models.CharField.register_lookup(Length)


class Family(models.Model):
    name = models.CharField(max_length=255, unique=True)
    vernacular_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return ' '.join([self.name])

    class Meta:
        ordering = ['name']


class Genus(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return ' '.join([self.name, f'({self.family.name})'])

    class Meta:
        ordering = ['name']
        unique_together = ['family', 'name']
        verbose_name_plural = 'genera'


class Species(ClusterableModel):
    bloom_time_choices = [(' '.join([i, str(v)]), ' '.join([i, str(v)])) for _, v in MONTHS.items()
                          for i in ['Early', 'Mid', 'Late']] + \
                         [(v, v) for _, v in MONTHS.items()]

    genus = models.ForeignKey(Genus, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True, null=True)
    full_name = models.CharField(max_length=255)
    subspecies = models.CharField(max_length=255, blank=True, null=True)
    variety = models.CharField(max_length=255, blank=True, null=True)
    subvariety = models.CharField(max_length=255, blank=True, null=True)
    forma = models.CharField(max_length=255, blank=True, null=True)
    subforma = models.CharField(max_length=255, blank=True, null=True)
    cultivar = models.CharField(max_length=255, blank=True, null=True)
    vernacular_name = models.CharField(max_length=255)
    habit = models.CharField(max_length=255, blank=True, null=True)
    hardiness = ArrayField(base_field=models.PositiveSmallIntegerField(validators=[MinValueValidator(1),
                                                                                   MaxValueValidator(13)]),
                           size=13, blank=True, null=True)
    water_regime = models.CharField(max_length=255, blank=True, null=True)
    exposure = models.CharField(max_length=255, blank=True, null=True)
    bloom_time = ArrayField(base_field=models.CharField(choices=bloom_time_choices, max_length=255), blank=True,
                            null=True)
    plant_size = models.CharField(max_length=255, blank=True, null=True)
    flower_color = models.CharField(max_length=255, blank=True, null=True)
    utah_native = models.BooleanField(default=False)
    plant_select = models.BooleanField(default=False)
    deer_resist = models.BooleanField(default=False)
    rabbit_resist = models.BooleanField(default=False)
    bee_friend = models.BooleanField(default=False)
    high_elevation = models.BooleanField(default=False)

    panels = [
        InlinePanel('species_images', label='Species Images'),
        FieldPanel('genus'),
        FieldPanel('name'),
        FieldPanel('full_name'),
        FieldPanel('subspecies'),
        FieldPanel('variety'),
        FieldPanel('subvariety'),
        FieldPanel('forma'),
        FieldPanel('subforma'),
        FieldPanel('cultivar'),
        FieldPanel('vernacular_name'),
        FieldPanel('habit'),
        FieldPanel('hardiness'),
        FieldPanel('water_regime'),
        FieldPanel('exposure'),
        FieldPanel('bloom_time'),
        FieldPanel('plant_size'),
        FieldPanel('flower_color'),
        FieldPanel('utah_native'),
        FieldPanel('plant_select'),
        FieldPanel('deer_resist'),
        FieldPanel('rabbit_resist'),
        FieldPanel('bee_friend'),
        FieldPanel('high_elevation')
    ]

    def __str__(self):
        return self.full_name

    class Meta:
        ordering = ['full_name']
        unique_together = ['genus', 'name', 'subspecies', 'variety', 'subvariety', 'forma', 'subforma', 'cultivar']
        verbose_name_plural = 'species'
        constraints = [
            models.CheckConstraint(check=models.Q(vernacular_name__length__gt=0), name='vernacular_name_not_empty'),
            models.CheckConstraint(check=models.Q(full_name__length__gt=0), name='full_name_not_empty')
        ]


class SpeciesImage(Orderable):
    species = ParentalKey(Species, on_delete=models.CASCADE, related_name='species_images')
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+'
    )
    caption = models.CharField(blank=True, max_length=250)
    copyright = models.CharField(blank=True, max_length=300)

    panels = [
        FieldPanel('image'),
        FieldPanel('caption'),
        FieldPanel('copyright'),
    ]


class Location(models.Model):
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    class Meta:
        unique_together = ['latitude', 'longitude']

    def __str__(self):
        return ', '.join([str(self.latitude), str(self.longitude)])


class GardenArea(models.Model):
    area: str = models.CharField(max_length=255, blank=True, null=True)  # Garden Area/Zone in BRAHMS
    name: str = models.CharField(max_length=255, blank=True, null=True)  # Garden Location in BRAHMS
    code: str = models.CharField(max_length=20, blank=True, null=True, unique=True)  # Garden Location Code in BRAHMS

    def __str__(self):
        return '\n'.join([self.area, self.name, self.code])


class Collection(models.Model):
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, blank=True, null=True)
    garden = models.ForeignKey(GardenArea, on_delete=models.SET_NULL, null=True)
    species = models.ForeignKey(Species, on_delete=models.CASCADE)
    plant_date = models.DateField(blank=True, null=True)
    plant_id = models.CharField(max_length=255, unique=True)
    commemoration_category = models.CharField(max_length=255, null=True, blank=True)
    commemoration_person = models.CharField(max_length=255, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return self.plant_id


class BloomEvent(models.Model):
    """
    A model to represent a bloom event for a species and/or collections.
    """
    title = models.CharField(max_length=255, blank=True, null=True, help_text=_(
        'Optional title to describe what\'s blooming. If left blank, the species name will be used.'))
    description = models.TextField(blank=True, null=True, help_text=_(
        'Optional description of what is blooming, where to see it and any other relevant info you think people might find interesting.'))
    url = models.URLField(blank=True, null=True, help_text=_(
        'Optionally link to a related Blooming Now post. If left blank and species is set a link to the plant map filtered to that species will be automatically generated.'))
    species = models.ForeignKey(Species, on_delete=models.SET_NULL, blank=True, null=True)
    collections = models.ManyToManyField(Collection, blank=True)
    bloom_start = models.DateField(blank=True, null=True)
    bloom_end = models.DateField(blank=True, null=True, help_text=_(
        'If left blank, the bloom start date will be used as the end date when displayed on calendars.'))
    area = models.ForeignKey(GardenArea, on_delete=models.SET_NULL, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    panels = [
        FieldPanel('title'),
        FieldPanel('description'),
        FieldPanel('url'),
        FieldPanel('species'),
        FieldPanel('collections'),
        FieldPanel('bloom_start'),
        FieldPanel('bloom_end'),
        FieldPanel('area'),
    ]

    def __str__(self):
        return self.title if self.title else f'Bloom Event for {self.species.full_name if self.species else "Unknown Species"}'

    def save(self, *args, **kwargs):
        # If a title is not set, use the species name as the title
        if not self.title and (self.species or self.collections.exists()):
            if self.species:
                self.title = f'Bloom Event for {self.species.full_name}'
            elif self.collections.exists():
                species_names = set(collection.species.full_name for collection in self.collections.all())
                if len(species_names) == 1:
                    self.title = f'Bloom Event for {species_names.pop()}'
                else:
                    self.title = f'Bloom Event for Multiple Species'

        # If a URL is not set, generate one based on the species
        if not self.url:
            if self.species:
                self.url = f'https://redbuttegarden.org/plants/plant-map/?scientific_name={urllib.parse.quote(self.species.full_name)}'

        super().save(*args, **kwargs)
