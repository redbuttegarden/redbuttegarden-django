import os

from django.core.files.images import ImageFile
from rest_framework import generics, permissions, viewsets, status

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from PIL import Image as PILImage
from rest_framework.decorators import api_view
from rest_framework.response import Response
from wagtail.images.models import Image

from .models import Family, Genus, Species, Collection, Location
from .serializers import FamilySerializer, SpeciesSerializer, CollectionSerializer, GenusSerializer, \
    LocationSerializer


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

class SpeciesList(generics.ListCreateAPIView):
    queryset = Species.objects.all()
    serializer_class = SpeciesSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class SpeciesDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Species.objects.all()
    serializer_class = SpeciesSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class LocationViewSet(viewsets.ModelViewSet):
    """
    List, create, retrieve, update or delete locations.
    """
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
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


@api_view(['PUT'])
def set_species_image(request):
    """
    Endpoint to allow dummy wagtail images to be associated with existing Species
    objects. The dummy images can later be replaced with real images by manually
    uploading to S3, thus circumventing the cost of uploading directly thru the
    AWS Gateway.
    """
    genus_name = request.data.get('species', {}).get('genus', {}).get('name')
    species_name = request.data.get('species', {}).get('name')
    cultivar = request.data.get('species', {}).get('cultivar')
    vernacular_name = request.data.get('species', {}).get('vernacular_name')

    try:
        genus = Genus.objects.get(name=genus_name)
    except Genus.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    try:
        species = Species.objects.get(genus=genus,
                                      name=species_name,
                                      cultivar=cultivar,
                                      vernacular_name=vernacular_name)
    except Species.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        img_title = '_'.join([genus_name,
                              species_name,
                              cultivar,
                              vernacular_name])
        file_name = img_title.replace(' ', '-') + '.jpeg'

        # Create empty dummy file that can later be replaced with a real image
        img_path = os.path.join(settings.MEDIA_ROOT, 'plant_images', file_name)
        pil_img = PILImage.new(mode='RGB', size=(1, 1))
        pil_img.save(img_path)
        img_file = ImageFile(open(img_path, 'rb'), name=file_name)
        wag_img = Image.objects.create(title=img_title, file=img_file, width=1, height=1)
        species.image = wag_img
        species.save()
        return Response(status=status.HTTP_200_OK)


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
