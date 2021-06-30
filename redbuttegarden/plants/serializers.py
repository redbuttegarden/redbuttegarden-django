from django.contrib.postgres.validators import ArrayMaxLengthValidator
from rest_framework import serializers

from plants.models import Collection, Family, Genus, Location, Species

"""
Empty validator lists are defined for fields with unique constraints
so that Collection objects can be created when nested objects already
exist.
"""
class FamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = ['id', 'name']
        extra_kwargs = {
            'name': {
                'validators': []
            }
        }

class GenusSerializer(serializers.ModelSerializer):
    family = FamilySerializer()

    class Meta:
        model = Genus
        fields = ['id', 'family', 'name']
        extra_kwargs = {
            'name': {
                'validators': []
            }
        }

class SpeciesSerializer(serializers.ModelSerializer):
    genus = GenusSerializer()
    hardiness = serializers.ListField(allow_empty=True, allow_null=True,
                                      child=serializers.IntegerField(label='Hardiness',
                                                                     max_value=13,
                                                                     min_value=1),
                                      validators=[ArrayMaxLengthValidator()])

    class Meta:
        model = Species
        fields = ['id', 'genus', 'name', 'cultivar', 'vernacular_name', 'habit', 'hardiness', 'water_regime']
        extra_kwargs = {
            'name': {
                'validators': []
            }
        }

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'latitude', 'longitude']


class CollectionSerializer(serializers.ModelSerializer):
    species = SpeciesSerializer()
    location = LocationSerializer()
    plant_date = serializers.DateField(input_formats=['%d-%m-%Y'], required=False, allow_null=True)

    class Meta:
        model = Collection
        fields = ['id', 'species', 'location', 'plant_date', 'planter', 'created_on', 'last_modified']


    def create(self, validated_data):
        species_data = validated_data.pop('species')
        genus_data = species_data.pop('genus')
        family_data = genus_data.pop('family')
        location_data = validated_data.pop('location')

        family, _ = Family.objects.get_or_create(**family_data)
        genus, _ = Genus.objects.get_or_create(family=family, **genus_data)
        # TODO - Catch errors when species data are changed
        # Get or create logic doesn't seem to avoid unique constraint between genus/species name
        try:
            species = Species.objects.get(genus=genus, name=species_data['name'])
        except Species.DoesNotExist:
            species = Species(genus=genus, **species_data)
            species.save()

        location, _ = Location.objects.get_or_create(**location_data)
        collection, _ = Collection.objects.get_or_create(location=location, species=species, **validated_data)

        return collection
