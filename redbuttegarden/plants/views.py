import logging
from collections import OrderedDict

from django.http import JsonResponse
from django.utils.dates import MONTHS
from django.middleware.csrf import get_token
from rest_framework import generics, viewsets, status

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

    def get_queryset(self):
        queryset = Species.objects.all()

        name = self.request.query_params.get('name')
        cultivar = self.request.query_params.get('cultivar')
        vernacular_name = self.request.query_params.get('vernacular_name')
        genus = self.request.query_params.get('genus')

        if name:
            queryset = queryset.filter(name=name)
        if cultivar:
            queryset = queryset.filter(cultivar=cultivar)
        if vernacular_name:
            queryset = queryset.filter(vernacular_name=vernacular_name)
        if genus:
            queryset = queryset.filter(genus__name=genus)

        return queryset


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


def set_image(request, pk):
    # Check if user has a valid API Token
    try:
        token = request.META['HTTP_AUTHORIZATION'].split(' ')[1]
    except KeyError:
        return JsonResponse({'status': 'failure'})
    if Token.objects.filter(key=token).exists():
        species = Species.objects.get(pk=pk)
        uploaded_image = request.FILES.get('image')
        img_title = '_'.join([species.genus.name,
                              species.name if species.name else '',
                              species.cultivar if species.cultivar else '',
                              uploaded_image.name])
        image, img_created = Image.objects.get_or_create(
            file=uploaded_image,
            defaults={'title': img_title}
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
    # Flower color list of lists
    flower_colors = [species['flower_color'].split(',') for species in
                     Species.objects.order_by('flower_color').values('flower_color').distinct('flower_color')
                     if species['flower_color'] is not '' and species['flower_color'] is not None]
    flower_colors = [color for colors in flower_colors for color in colors]  # Flattens list of lists
    flower_colors = sorted(list(OrderedDict.fromkeys(flower_colors)))  # Removes duplicates
    commemoration_people = [collection['commemoration_person'] for collection in
                            Collection.objects.order_by('commemoration_person').values('commemoration_person').distinct('commemoration_person')
                            if collection['commemoration_person'] is not ''
                            and collection['commemoration_person'] is not None]
    context = {
        'families': families,
        'habits': habits,
        'exposures': exposures,
        'water_needs': water_needs,
        'bloom_months': list(MONTHS.values()),
        'flower_colors': flower_colors,
        'commemoration_people': commemoration_people
    }
    return render(request, 'plants/collection_search.html', context)
