from django.contrib.auth.mixins import UserPassesTestMixin
from rest_framework import generics, viewsets

from django.shortcuts import render, get_object_or_404

from .models import Family, Genus, Species, Collection, Location
from .serializers import FamilySerializer, SpeciesSerializer, CollectionSerializer, GenusSerializer, LocationSerializer


class TestAPIGroupMembership(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.groups.filter(name='API').exists()

class FamilyViewSet(TestAPIGroupMembership, viewsets.ModelViewSet):
    """
    List, create, retrieve, update or delete families.
    """
    queryset = Family.objects.all()
    serializer_class = FamilySerializer

class GenusViewSet(TestAPIGroupMembership, viewsets.ModelViewSet):
    """
    List, create, retrieve, update or delete genera.
    """
    queryset = Genus.objects.all()
    serializer_class = GenusSerializer

class SpeciesList(TestAPIGroupMembership, generics.ListCreateAPIView):
    queryset = Species.objects.all()
    serializer_class = SpeciesSerializer

class SpeciesDetail(TestAPIGroupMembership, generics.RetrieveUpdateDestroyAPIView):
    queryset = Species.objects.all()
    serializer_class = SpeciesSerializer

class LocationViewSet(TestAPIGroupMembership, viewsets.ModelViewSet):
    """
    List, create, retrieve, update or delete locations.
    """
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

class CollectionList(TestAPIGroupMembership, generics.ListCreateAPIView):
    """
    List 100 most recently created collections, or create new collections.
    """
    queryset = Collection.objects.all().order_by('-id')[:100]
    serializer_class = CollectionSerializer

class CollectionDetail(TestAPIGroupMembership, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a living plant collection.
    """
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer

def get_token(request):
    return render(request, 'plants/token.html')

def plant_map_view(request):
    return render(request, 'plants/collection_map.html')

def collection_detail(request, collection_id):
    collection = get_object_or_404(Collection, pk=collection_id)
    return render(request, 'plants/collection_detail.html', {'collection': collection})

def species_detail(request, species_id):
    species = get_object_or_404(Species, pk=species_id)
    return render(request, 'plants/species_detail.html', {'species': species})
