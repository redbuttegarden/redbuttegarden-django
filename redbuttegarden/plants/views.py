import logging
import os
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.search import SearchVector
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponseRedirect
from django.middleware.csrf import get_token
from django.urls import reverse
from geojson import dumps
from rest_framework import generics, viewsets, status

from django.shortcuts import render, get_object_or_404, redirect
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view
from rest_framework.response import Response
from wagtail.core.models import Collection as WagtailCollection
from wagtail.images.models import Image

from .forms import CollectionSearchForm, FeedbackReportForm
from .models import Family, Genus, Species, Collection, Location, SpeciesImage
from .serializers import FamilySerializer, SpeciesSerializer, CollectionSerializer, GenusSerializer, \
    LocationSerializer
from .utils import get_feature_collection, style_message

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

        genus = self.request.query_params.get('genus')
        name = self.request.query_params.get('name')
        subspecies = self.request.query_params.get('subspecies')
        variety = self.request.query_params.get('variety')
        subvariety = self.request.query_params.get('subvariety')
        forma = self.request.query_params.get('forma')
        subforma = self.request.query_params.get('subforma')
        cultivar = self.request.query_params.get('cultivar')

        if genus:
            queryset = queryset.filter(genus__name=genus)
        if name:
            queryset = queryset.filter(name=name)
        if subspecies:
            queryset = queryset.filter(subspecies=subspecies)
        if variety:
            queryset = queryset.filter(variety=variety)
        if subvariety:
            queryset = queryset.filter(subvariety=subvariety)
        if forma:
            queryset = queryset.filter(forma=forma)
        if subforma:
            queryset = queryset.filter(subforma=subforma)
        if cultivar:
            queryset = queryset.filter(cultivar=cultivar)


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


@api_view(['POST'])
def set_image(request, pk):
    # Check if user has a valid API Token
    try:
        token = request.META['HTTP_AUTHORIZATION'].split(' ')[1]
    except KeyError:
        return JsonResponse({'status': 'failure'})
    if Token.objects.filter(key=token).exists():
        if 'copyright_info' in request.data:
            copyright_text = request.data['copyright_info']
        else:
            copyright_text = ''

        species = Species.objects.get(pk=pk)
        uploaded_image = request.FILES.get('image')
        img_title = uploaded_image.name

        try:
            image, img_created = Image.objects.get_or_create(
                title=img_title,
                defaults={'file': uploaded_image,
                          'collection': WagtailCollection.objects.get(name='BRAHMS Data')}
            )
        except WagtailCollection.DoesNotExist:
            logger.error('"BRAHMS DATA" Collection is missing. Unable to save new images.')
            return JsonResponse({'status': 'failure'})

        if img_created:
            image.tags.add('BRAHMS')

        species_image, species_img_created = SpeciesImage.objects.get_or_create(
            species=species,
            image=image,
            copyright=copyright_text,
            defaults={'caption': species.full_name}
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
        garden_name = request.GET.get('garden_name', None)
        habit = request.GET.get('habits', None)
        exposure = request.GET.get('exposures', None)
        water_need = request.GET.get('water_needs', None)
        bloom_month = request.GET.get('bloom_months', None)
        flower_color = request.GET.get('flower_colors', None)
        memorial_person = request.GET.get('memorial_person', None)
        utah_native = request.GET.get('utah_native', None)
        plant_select = request.GET.get('plant_select', None)
        deer_resistant = request.GET.get('deer_resistant', None)
        rabbit_resistant = request.GET.get('rabbit_resistant', None)
        bee_friendly = request.GET.get('bee_friendly', None)
        high_elevation = request.GET.get('high_elevation', None)
        available_memorial = request.GET.get('available_memorial', None)

        if scientific_name:
            collections = collections.filter(species__full_name__icontains=scientific_name)
        if common_name:
            collections = collections.annotate(search=SearchVector('species__cultivar',
                                                                   'species__vernacular_name'))
        if family:
            collections = collections.filter(species__genus__family_id=family)
        if garden_name:
            collections = collections.filter(garden__name=garden_name)
        if habit:
            collections = collections.filter(species__habit=habit)
        if exposure:
            collections = collections.filter(species__exposure=exposure)
        if water_need:
            collections = collections.filter(species__water_regime=water_need)
        if bloom_month:
            mods = ['Early', 'Mid', 'Late']
            month = [' '.join([mod, bloom_month]) for mod in mods]
            month.append(bloom_month)
            collections = collections.filter(species__bloom_time__overlap=month)
        if flower_color:
            collections = collections.filter(species__flower_color__icontains=flower_color)
        if memorial_person:
            collections = collections.filter(commemoration_person=memorial_person)
        if utah_native:
            collections = collections.filter(species__utah_native=utah_native)
        if plant_select:
            collections = collections.filter(species__plant_select=plant_select)
        if deer_resistant:
            collections = collections.filter(species__deer_resist=deer_resistant)
        if rabbit_resistant:
            collections = collections.filter(species__rabbit_resist=rabbit_resistant)
        if bee_friendly:
            collections = collections.filter(species__bee_friend=bee_friendly)
        if high_elevation:
            collections = collections.filter(species__high_elevation=high_elevation)
        if available_memorial:
            collections = collections.filter(commemoration_category='Available')


        feature_collection = get_feature_collection(collections)
        collection_geojson = dumps(feature_collection)
        return JsonResponse(collection_geojson, safe=False)
    mapbox_api_token = getattr(settings, 'MAPBOX_API_TOKEN', None)
    return render(request, 'plants/collection_map.html', {'mapbox_token': mapbox_api_token})

def collection_detail(request, collection_id):
    """
    View for displaying detailed info about a single Collection object.
    """
    collection = get_object_or_404(Collection, pk=collection_id)
    mapbox_api_token = getattr(settings, 'MAPBOX_API_TOKEN', None)
    return render(request, 'plants/collection_detail.html', {'collection': collection,
                                                             'mapbox_token': mapbox_api_token})

def species_detail(request, species_id):
    """
    View for displaying detailed info about a single Species object.
    """
    species = get_object_or_404(Species, pk=species_id)
    species_images = SpeciesImage.objects.filter(species=species)
    return render(request, 'plants/species_detail.html', {'species': species,
                                                          'images': species_images})

def species_or_collection_feedback(request, species_id=None, collection_id=None):
    """
    Form view for reporting a problem with a Species or Collection object.
    """
    species = None
    collection = None
    if species_id:
        species = get_object_or_404(Species, pk=species_id)
    elif collection_id:
        collection = get_object_or_404(Collection, pk=collection_id)
    else:
        raise ValueError('Missing ID to Species or Collection')

    if request.method == 'POST':
        form = FeedbackReportForm(species_id, collection_id, request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            original_message = form.cleaned_data['message']
            sender = form.cleaned_data['sender']
            cc_myself = form.cleaned_data['cc_myself']

            recipients = [user.email for user in get_user_model().objects.filter(
                groups__name='Plant Collection Curators')]
            if cc_myself:
                recipients.append(sender)

            subject = 'RBG Website Plants Feedback: ' + subject
            message = style_message(request, species, collection, original_message)
            send_mail(subject, message, sender, recipients)
            return HttpResponseRedirect(reverse('plants:feedback-thanks'))
    else:
        form = FeedbackReportForm(species_id, collection_id)

    context = {
        'form': form,
        'species_id': species_id,
        'collection_id': collection_id
    }
    return render(request, 'plants/plant_feedback.html', context)


def collection_search(request):
    """
    View for filtering Collection objects to be displayed on the plant map.
    """
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


def feedback_thanks(request):
    return render(request, 'plants/feedback_thanks.html')
