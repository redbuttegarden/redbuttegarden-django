from rest_framework import generics, viewsets, status
from django.middleware.csrf import get_token
from django.shortcuts import render, get_object_or_404
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response

from .models import Family, Genus, Species, Collection, Location
from .serializers import FamilySerializer, SpeciesSerializer, CollectionSerializer, GenusSerializer, LocationSerializer


class FamilyViewSet(viewsets.ModelViewSet):
    """
    List, create, retrieve, update or delete families.
    """
    queryset = Family.objects.all()
    serializer_class = FamilySerializer

class GenusViewSet(viewsets.ModelViewSet):
    """
    List, create, retrieve, update or delete genera.
    """
    queryset = Genus.objects.all()
    serializer_class = GenusSerializer

class SpeciesList(generics.ListCreateAPIView):
    queryset = Species.objects.all()
    serializer_class = SpeciesSerializer

class SpeciesDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Species.objects.all()
    serializer_class = SpeciesSerializer

class LocationViewSet(viewsets.ModelViewSet):
    """
    List, create, retrieve, update or delete locations.
    """
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

class CollectionList(generics.ListCreateAPIView):
    """
    List 100 most recently created collections, or create new collections.
    """
    queryset = Collection.objects.all().order_by('-id')[:100]
    serializer_class = CollectionSerializer

class CollectionDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a living plant collection.
    """
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer

class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        if user.groups.filter(name='API').exists():
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'csrf_token': get_token(request),
            })
        return Response(status=status.HTTP_403_FORBIDDEN)

def plant_map_view(request):
    return render(request, 'plants/collection_map.html')

def collection_detail(request, collection_id):
    collection = get_object_or_404(Collection, pk=collection_id)
    return render(request, 'plants/collection_detail.html', {'collection': collection})

def species_detail(request, species_id):
    species = get_object_or_404(Species, pk=species_id)
    return render(request, 'plants/species_detail.html', {'species': species})
