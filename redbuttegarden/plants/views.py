from rest_framework import generics, permissions, viewsets

from .models import Family, Genus, Species, Collection
from .serializers import FamilySerializer, SpeciesSerializer, CollectionSerializer, GenusSerializer


class FamilyViewSet(viewsets.ModelViewSet):
    """
    List, create, retrieve, update or delete families.
    """
    queryset = Family.objects.all()
    serializer_class = FamilySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class GenusViewSet(viewsets.ModelViewSet):
    """
    List, create, retrieve, update or delete genera.
    """
    queryset = Genus.objects.all()
    serializer_class = GenusSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class SpeciesDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Species.objects.all()
    serializer_class = SpeciesSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class CollectionList(generics.ListCreateAPIView):
    """
    List 100 most recently created collections, or create new collections.
    """
    queryset = Collection.objects.all().order_by('-id')[:100]
    serializer_class = CollectionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CollectionDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a living plant collection.
    """
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
