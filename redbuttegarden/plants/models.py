from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models.functions import Length
from django.utils.dates import MONTHS
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel
from wagtail.core.models import Orderable
from wagtail.images.edit_handlers import ImageChooserPanel

models.CharField.register_lookup(Length)


class Family(models.Model):
    name = models.CharField(max_length=255, unique=True)
    vernacular_name = models.CharField(max_length=255, blank=True, null=True)

    def __repr__(self):
        return ' '.join([self.name])

    class Meta:
        ordering = ['name']

class Genus(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return ' '.join([self.name, f'({self.family.name})'])

    class Meta:
        ordering = ['name']

class Species(ClusterableModel):
    bloom_time_choices = [(v, v) for _, v in MONTHS.items()]

    genus = models.ForeignKey(Genus, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True, null=True)
    subspecies = models.CharField(max_length=255, blank=True, null=True)
    variety = models.CharField(max_length=255, blank=True, null=True)
    subvariety = models.CharField(max_length=255, blank=True, null=True)
    forma = models.CharField(max_length=255, blank=True, null=True)
    subforma = models.CharField(max_length=255, blank=True, null=True)
    cultivar = models.CharField(max_length=255, blank=True, null=True)
    vernacular_name = models.CharField(max_length=255)
    habit = models.CharField(max_length=255)
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
        if self.cultivar and self.name:
            return ' '.join([self.genus.name, self.name, "'" + self.cultivar + "'"])

        if self.cultivar and not self.name:
            return ' '.join([self.genus.name, "'" + self.cultivar + "'"])

        if self.name and not self.cultivar:
            return ' '.join([self.genus.name, self.name])

        return ' '.join([self.genus.name, self.vernacular_name])

    class Meta:
        ordering = ['name']
        unique_together = ['genus', 'name', 'subspecies', 'variety', 'subvariety', 'forma', 'subforma', 'cultivar']
        verbose_name_plural = 'species'
        constraints = [
            models.CheckConstraint(check=models.Q(vernacular_name__length__gt=0), name='vernacular_name_not_empty')
        ]

class SpeciesImage(Orderable):
    species = ParentalKey(Species, on_delete=models.CASCADE, related_name='species_images')
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+'
    )
    caption = models.CharField(blank=True, max_length=250)
    copyright = models.CharField(blank=True, max_length=300)

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('caption'),
        FieldPanel('copyright'),
    ]

class Location(models.Model):
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    class Meta:
        unique_together = ['latitude', 'longitude']

    def __str__(self):
        return ' '.join([str(self.latitude), str(self.longitude)])

class GardenArea(models.Model):
    area = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    code = models.CharField(max_length=20, blank=True, null=True, unique=True)

class Collection(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    garden = models.ForeignKey(GardenArea, on_delete=models.SET_NULL, null=True)
    species = models.ForeignKey(Species, on_delete=models.CASCADE)
    plant_date = models.DateField(blank=True, null=True)
    plant_id = models.CharField(max_length=255, null=True, blank=True)
    commemoration_category = models.CharField(max_length=255, null=True, blank=True)
    commemoration_person = models.CharField(max_length=255, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return self.plant_id
