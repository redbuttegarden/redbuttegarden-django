from rest_framework import serializers

from plants.models import Collection, Family, Genus, Location, Species
from .custom_fields import StringArrayField


class FamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = ['name']

class GenusSerializer(serializers.HyperlinkedModelSerializer):
    family = serializers.HyperlinkedRelatedField(read_only=True, view_name='family-detail')

    class Meta:
        model = Genus
        fields = ['url', 'id', 'family', 'name']

class SpeciesSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    cultivar = serializers.CharField(max_length=255)
    vernacular_name = serializers.CharField(max_length=255)
    habit = serializers.CharField(max_length=255)
    hardiness = StringArrayField()
    water_regime = serializers.CharField(max_length=255)
    exposure = serializers.CharField(max_length=255)
    bloom_time = StringArrayField()
    plant_size = serializers.CharField(max_length=255)

    def create(self, validated_data):
        return Species.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.cultivar = validated_data.get('cultivar', instance.cultivar)
        instance.vernacular_name = validated_data.get('vernacular_name', instance.vernacular_name)
        instance.habit = validated_data.get('habit', instance.habit)
        instance.hardiness = validated_data.get('hardiness', instance.hardiness)
        instance.water_regime = validated_data.get('water_regime', instance.water_regime)
        instance.exposure = validated_data.get('exposure', instance.exposure)
        instance.bloom_time = validated_data.get('bloom_time', instance.bloom_time)
        instance.plant_size = validated_data.get('plant_size', instance.plant_size)

        instance.save()
        return instance

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        models = Location
        fields = ['latitude', 'longitude']


class CollectionSerializer(serializers.HyperlinkedModelSerializer):
    species = serializers.HyperlinkedRelatedField(read_only=True, view_name='species-detail')
    location = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Collection
        fields = ['url', 'id', 'species', 'location', 'plant_date', 'planter']
