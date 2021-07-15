import logging

from django.http import JsonResponse
from django.utils.dates import MONTHS
from django.middleware.csrf import get_token
from rest_framework import generics, permissions, viewsets, status

from django.shortcuts import render, get_object_or_404
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from wagtail.images.models import Image

from .models import Family, Genus, Species, Collection, Location, SpeciesImage
from .serializers import FamilySerializer, SpeciesSerializer, CollectionSerializer, GenusSerializer, \
    LocationSerializer

logger = logging.getLogger(__name__)


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


def csrf_view(request):
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
