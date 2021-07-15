import logging
import os

from django.http import JsonResponse
from django.utils.dates import MONTHS
from django.middleware.csrf import get_token
from django.core.files.images import ImageFile
from rest_framework import generics, permissions, viewsets, status

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from PIL import Image as PILImage
from rest_framework.decorators import api_view
from rest_framework.response import Response
from wagtail.images.models import Image

from .models import SpeciesImage

logger = logging.getLogger(__name__)
from .models import Family, Genus, Species, Collection, Location
from .serializers import FamilySerializer, SpeciesSerializer, CollectionSerializer, GenusSerializer, \
    LocationSerializer


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
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

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


def set_image(request, pk):
    # Check if user has a valid API Token
    try:
        token = request.META['Authorization'].split(' ')[1]
    except KeyError:
        return JsonResponse({'status': 'failure'})
    if Token.objects.get(key=token).exists():
        species = Species.objects.get(pk=pk)
        uploaded_image = request.FILES.get('image')
        image, img_created = Image.objects.get_or_create(
            title='_'.join([species.genus.name,
                            species.name,
                            species.cultivar]),
            defaults={'file': uploaded_image}
        )
        species_image, species_img_created = SpeciesImage.objects.get_or_create(
            species=species,
            image=image,
            caption=''
        )

        return JsonResponse({'status': 'success',
                             'image_created': img_created,
                             'species_image_created': species_img_created})

    return JsonResponse({'status': 'failure'})



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
    species_images = SpeciesImage.objects.filter(species=species)
    return render(request, 'plants/species_detail.html', {'species': species,
                                                          'images': species_images})

def collection_search(request):
    families = [family['name'] for family in Family.objects.values('name').distinct()]
    habits = [species['habit'] for species in Species.objects.order_by('habit').values('habit').distinct('habit')]
    exposures = [species['exposure'] for species in
                Species.objects.order_by('exposure').values('exposure').distinct('exposure')
                 if species['exposure'] is not '' and species['exposure'] is not None]
    water_needs = [species['water_regime'] for species in
                   Species.objects.order_by('water_regime').values('water_regime').distinct('water_regime')]
    context = {
        'families': families,
        'habits': habits,
        'exposures': exposures,
        'water_needs': water_needs,
        'bloom_months': list(MONTHS.values()),

    }
    return render(request, 'plants/collection_search.html', context)
