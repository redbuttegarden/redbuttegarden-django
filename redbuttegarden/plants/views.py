import logging
from collections import OrderedDict

from django.http import JsonResponse
from django.utils.dates import MONTHS
from django.middleware.csrf import get_token
from geojson import Feature, Point, FeatureCollection, dumps
from rest_framework import generics, viewsets, status

from django.shortcuts import render, get_object_or_404, redirect
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from wagtail.images.models import Image

from .forms import CollectionSearchForm
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
    collections = Collection.objects.all()
    family = request.session.get('family', None)
    if family:
        collections = [collection for collection in collections.filter(species__genus__family__name_icontains=family)]

    features = []
    for collection in collections:
        feature = Feature(geometry=Point((collection.location.longitude,
                                          collection.location.latitude)),
                          properties={
                              'id': collection.id,
                              'family_name': collection.species.genus.family.name,
                              'genus_name': collection.species.genus.name,
                              'species_name': collection.species.name,
                              'cultivar': collection.species.cultivar,
                              'vernacular_name': collection.species.vernacular_name,
                              'habit': collection.species.habit,
                              'hardiness': collection.species.hardiness,
                              'water_regime': collection.species.water_regime,
                              'exposure': collection.species.exposure,
                              'boom_time': collection.species.bloom_time,
                              'plant_size': collection.species.plant_size,
                              'planted_on': collection.plant_date.strftime('%m/%d/%Y')
                              if collection.plant_date else None,
                          })
        features.append(feature)

    feature_collection = FeatureCollection(features)
    collection_geojson = dumps(feature_collection)
    return render(request, 'plants/collection_map.html', {'geojson': collection_geojson})

def collection_detail(request, collection_id):
    collection = get_object_or_404(Collection, pk=collection_id)
    return render(request, 'plants/collection_detail.html', {'collection': collection})

def species_detail(request, species_id):
    species = get_object_or_404(Species, pk=species_id)
    species_images = SpeciesImage.objects.filter(species=species)
    return render(request, 'plants/species_detail.html', {'species': species,
                                                          'images': species_images})

def collection_search(request):
    if request.method == 'POST':
        form = CollectionSearchForm(request.POST)
        if form.is_valid():
            request.session['family'] = form.cleaned_data['family_name']
            return redirect('plants:plant-map')
    else:
        form = CollectionSearchForm()

        context = {
            'form': form
        }
        return render(request, 'plants/collection_search.html', context)
