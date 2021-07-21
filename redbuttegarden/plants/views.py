import logging
from urllib.parse import urlencode

from django.contrib.postgres.search import SearchVector
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.urls import reverse
from geojson import dumps
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
from .utils import get_feature_collection

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
    if request.is_ajax() and request.method == 'GET':
        collections = Collection.objects.all()

        scientific_name = request.GET.get('scientific_name', None)
        common_name = request.GET.get('common_name', None)
        family = request.GET.get('family_name', None)
        habit = request.GET.get('habits', None)
        exposure = request.GET.get('exposures', None)
        water_need = request.GET.get('water_needs', None)
        bloom_month = request.GET.get('bloom_months', None)
        flower_color = request.GET.get('flower_colors', None)
        memorial_person = request.GET.get('memorial_person', None)
        utah_native = request.GET.get('utah_native', None)
        available_memorial = request.GET.get('available_memorial', None)

        if scientific_name:
            collections = collections.annotate(search=SearchVector('species__genus__name',
                                                                          'species__name')
                                                      .filter(search=scientific_name))
        if common_name:
            collections = collections.annotate(search=SearchVector('species__cultivar',
                                                                   'species__vernacular_name'))
        if family:
            collections = collections.filter(species__genus__family_id=family)
        if habit:
            collections = collections.filter(species__habit=habit)
        if exposure:
            collections = collections.filter(species__exposure=exposure)
        if water_need:
            collections = collections.filter(species__water_regime=water_need)
        if bloom_month:
            collections = collections.filter(species__bloom_time__contains=[bloom_month])
        if flower_color:
            collections = collections.filter(species__flower_color__search=flower_color)
        if memorial_person:
            collections = collections.filter(memorial_person=memorial_person)
        if utah_native:
            collections = collections.filter(species__utah_native=utah_native)
        if available_memorial:
            collections = collections.filter(commemoration_category='Available')


        feature_collection = get_feature_collection(collections)
        collection_geojson = dumps(feature_collection)
        return JsonResponse(collection_geojson, safe=False)
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
    if request.method == 'POST':
        form = CollectionSearchForm(request.POST)
        if form.is_valid():
            url = reverse('plants:plant-map')
            # Not false filter added to exclude boolean fields unless marked True
            params = {k: v for k, v in form.cleaned_data.items() if v is not ''
                      and v is not False}
            if params:
                url += '?' + urlencode(params)
            return redirect(url)
    else:
        form = CollectionSearchForm()

        context = {
            'form': form
        }
        return render(request, 'plants/collection_search.html', context)
