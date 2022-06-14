from rest_framework import serializers

from plants.models import Collection, Family, Genus, Location, Species, GardenArea

"""
Empty validator lists are defined for fields with unique constraints
so that Collection objects can be created when nested objects already
exist.
"""
class FamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = ['id', 'name', 'vernacular_name']
        extra_kwargs = {
            'name': {
                'validators': []
            }
        }

class GenusSerializer(serializers.ModelSerializer):
    family = FamilySerializer(required=False)

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
    habit = serializers.CharField(max_length=255, required=False)
    hardiness = serializers.ListField(allow_empty=True, allow_null=True,
                                      child=serializers.IntegerField(label='Hardiness',
                                                                     max_value=13,
                                                                     min_value=1),
                                      required=False)

    class Meta:
        model = Species
        fields = ['id', 'genus', 'name', 'full_name', 'subspecies', 'variety', 'subvariety', 'forma', 'subforma',
                  'cultivar', 'vernacular_name', 'habit', 'hardiness', 'water_regime', 'exposure', 'bloom_time',
                  'plant_size', 'flower_color', 'utah_native', 'plant_select', 'deer_resist', 'rabbit_resist',
                  'bee_friend', 'high_elevation']
        extra_kwargs = {
            'name': {
                'validators': []
            }
        }

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'latitude', 'longitude']

    def get_unique_together_validators(self):
        """Overriding method to disable unique together checks"""
        return []


class GardenSerializer(serializers.ModelSerializer):
    class Meta:
        model = GardenArea
        fields = ['id', 'area', 'name', 'code']
        extra_kwargs = {
            'code': {
                'validators': []
            }
        }


class CollectionSerializer(serializers.ModelSerializer):
    species = SpeciesSerializer()
    location = LocationSerializer()
    garden = GardenSerializer()
    plant_date = serializers.DateField(input_formats=['%Y-%m-%d'], required=False, allow_null=True)

    class Meta:
        model = Collection
        fields = ['id', 'species', 'location', 'garden', 'plant_date', 'plant_id', 'commemoration_category',
                  'commemoration_person', 'created_on', 'last_modified']

        extra_kwargs = {
            'plant_id': {
                'validators': []
            }
        }

    def create(self, validated_data):
        species_data = validated_data.pop('species')
        genus_data = species_data.pop('genus')
        family_data = genus_data.pop('family')
        location_data = validated_data.pop('location')
        garden_data = validated_data.pop('garden')

        family, _ = Family.objects.get_or_create(**family_data)
        genus, _ = Genus.objects.get_or_create(family=family, **genus_data)
        # TODO - Catch errors when species data are changed
        species, _ = Species.objects.update_or_create(genus=genus,
                                                   name=species_data['name'],
                                                   subspecies=species_data['subspecies'],
                                                   variety=species_data['variety'],
                                                   subvariety=species_data['subvariety'],
                                                   forma=species_data['forma'],
                                                   subforma=species_data['subforma'],
                                                   cultivar=species_data['cultivar'],
                                                   defaults={
                                                       'full_name': species_data['full_name'],
                                                       'vernacular_name': species_data['vernacular_name'],
                                                       'habit': species_data['habit'],
                                                       'hardiness': species_data['hardiness'],
                                                       'water_regime': species_data['water_regime'],
                                                       'exposure': species_data['exposure'],
                                                       'bloom_time': species_data['bloom_time'],
                                                       'plant_size': species_data['plant_size'],
                                                       'flower_color': species_data['flower_color'],
                                                       'utah_native': species_data['utah_native'],
                                                       'plant_select': species_data['plant_select'],
                                                       'deer_resist': species_data['deer_resist'],
                                                       'bee_friend': species_data['bee_friend'],
                                                       'high_elevation': species_data['high_elevation']
                                                   })

        location, _ = Location.objects.get_or_create(**location_data)
        garden, _ = GardenArea.objects.get_or_create(**garden_data)
        collection, _ = Collection.objects.update_or_create(plant_id=validated_data['plant_id'],
                                                            defaults={
                                                                'location': location,
                                                                'garden': garden,
                                                                'species': species,
                                                                'plant_date': validated_data['plant_date'],
                                                                'commemoration_category': validated_data['commemoration_category'],
                                                                'commemoration_person': validated_data['commemoration_person']
                                                            })

        return collection
