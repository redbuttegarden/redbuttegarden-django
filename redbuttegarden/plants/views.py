import logging
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.db import IntegrityError
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseNotFound
from django.middleware.csrf import get_token
from django.urls import reverse
from geojson import dumps
from requests import HTTPError
from rest_framework import generics, viewsets, status
from django.shortcuts import render, get_object_or_404, redirect
from django_tables2 import RequestConfig
from django_tables2.paginators import LazyPaginator
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view
from rest_framework.response import Response
from wagtail.models import Collection as WagtailCollection
from wagtail.images.models import Image

from .tables import CollectionTable

from .forms import CollectionSearchForm, FeedbackReportForm
from .models import Family, Genus, Species, Collection, Location, SpeciesImage
from .serializers import FamilySerializer, SpeciesSerializer, CollectionSerializer, GenusSerializer, \
    LocationSerializer
from .utils import filter_by_parameter, get_feature_collection, style_message

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

        genus = self.request.query_params.get('genus', 'unspecified')
        name = self.request.query_params.get('name', 'unspecified')
        full_name = self.request.query_params.get('full_name', 'unspecified')
        subspecies = self.request.query_params.get('subspecies', 'unspecified')
        variety = self.request.query_params.get('variety', 'unspecified')
        subvariety = self.request.query_params.get('subvariety', 'unspecified')
        forma = self.request.query_params.get('forma', 'unspecified')
        subforma = self.request.query_params.get('subforma', 'unspecified')
        cultivar = self.request.query_params.get('cultivar', 'unspecified')

        if genus != 'unspecified':
            queryset = queryset.filter(genus__name=genus)
        if name != 'unspecified':
            queryset = queryset.filter(name=name)
        if full_name != 'unspecified':
            queryset = queryset.filter(full_name__icontains=full_name)
        if subspecies != 'unspecified':
            queryset = queryset.filter(subspecies=subspecies)
        if variety != 'unspecified':
            queryset = queryset.filter(variety=variety)
        if subvariety != 'unspecified':
            queryset = queryset.filter(subvariety=subvariety)
        if forma != 'unspecified':
            queryset = queryset.filter(forma=forma)
        if subforma != 'unspecified':
            queryset = queryset.filter(subforma=subforma)
        if cultivar != 'unspecified':
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
            logger.error(
                '"BRAHMS DATA" Collection is missing. Unable to save new images.')
            return JsonResponse({'status': 'failure'})

        if img_created:
            image.tags.add('BRAHMS')

        try:
            species_image, species_img_created = SpeciesImage.objects.get_or_create(
                species=species,
                image=image,
                copyright=copyright_text,
                defaults={'caption': species.full_name}
            )
        except IntegrityError:
            logger.debug(
                f'Failed to add image for species {species} ({pk}).\n\n\rImage: {image}\n\rCopyright: {copyright_text}')
            return JsonResponse({'status': 'failure',
                                 'image_created': img_created,
                                 'species_image_created': False})

        return JsonResponse({'status': 'success',
                             'image_created': img_created,
                             'species_image_created': species_img_created})

    return JsonResponse({'status': 'failure'})


def csrf_view(request):
    return render(request, 'plants/token.html')


def plant_map_view(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == 'GET':
        try:
            collections = filter_by_parameter(
                request, Collection.objects.exclude(location=None))
        except ValidationError:
            return JsonResponse(data={'message': 'Encountered error while parsing parameters.'}, status=400)

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

            hcaptcha_token = request.POST.get('h-captcha-response', None)

            # We use this to distinguish between requests error or hCaptcha error when hcaptcha_passed is False
            json_response = None

            try:
                # Make sure captcha is valid before we do anything else
                hcaptcha_response = requests.post('https://api.hcaptcha.com/siteverify',
                                                  data={'response': hcaptcha_token,
                                                        'secret': settings.HCAPTCHA_SECRET_KEY,
                                                        'sitekey': settings.HCAPTCHA_SITE_KEY},
                                                  headers={'Content-Type': 'application/x-www-form-urlencoded'})
                hcaptcha_response.raise_for_status()
                json_response = hcaptcha_response.json()
                logger.debug(f'hCaptcha Reponse: {json_response}')
                hcaptcha_passed = json_response['success']
            except HTTPError as e:
                logger.error(f'Error while checking hCaptcha response: {e}')
                messages.error(request, 'Error encountered while processing Captcha check. Please try again later.')
                hcaptcha_passed = False

            except Exception as e:
                logger.error(f'General exception occurred while processing hCaptcha response: {e}')
                messages.error(request, 'Error encountered while processing Captcha check. Please try again later.')
                hcaptcha_passed = False

            if hcaptcha_passed:
                recipients = [user.email for user in get_user_model().objects.filter(
                    groups__name='Plant Collection Curators')]

                subject = 'RBG Website Plants Feedback: ' + subject
                message = style_message(
                    request, species, collection, original_message)
                email = EmailMessage(subject=subject, body=message,
                                     from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'admin@redbuttegarden.org'),
                                     to=recipients, cc=(sender,) if cc_myself else None, reply_to=(sender,))
                email.send()
                return HttpResponseRedirect(reverse('plants:feedback-thanks'))
            else:
                # if json_response exists, must be an hCaptcha error
                if json_response:
                    logger.debug(f"Encountered hCaptcha error(s): {json_response['error-codes']}")
                    # Add non-field error to form
                    form.add_error(None,
                                   'We encountered an error while processing your Captcha challenge. Please try again.')

    else:
        form = FeedbackReportForm(species_id, collection_id)

    context = {
        'form': form,
        'species_id': species_id,
        'collection_id': collection_id,
        'hcaptcha_site_key': settings.HCAPTCHA_SITE_KEY,
    }
    return render(request, 'plants/plant_feedback.html', context)


def collection_search(request):
    """
    View for filtering Collection objects to be displayed on the plant map.
    """
    form = CollectionSearchForm()

    context = {
        'form': form
    }

    if request.method == 'POST':
        form = CollectionSearchForm(request.POST)
        if form.is_valid():
            # Not false filter added to exclude boolean fields unless marked True
            params = {k: v for k, v in form.cleaned_data.items() if v != ''
                      and v is not False}

            if 'map_search' in request.POST:
                url = reverse('plants:plant-map')
            elif 'list_search' in request.POST:
                url = reverse('plants:collection-list')
            else:
                return HttpResponseNotFound('Missing search type.')

            if params:
                url += '?' + urlencode(params)

            return redirect(url)
        else:
            messages.add_message(request, messages.ERROR,
                                 "Received invalid form data. Please edit your request and try again")

    return render(request, 'plants/collection_search.html', context)


def collection_list(request):
    if len(request.GET.keys()) == 0:
        collections = Collection.objects.all()
    else:
        collections = filter_by_parameter(request)

    table = CollectionTable(collections)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator}).configure(table)
    table.paginate(page=request.GET.get("page", 1), per_page=50)

    context = {
        'table': table
    }
    return render(request, 'plants/collection_list.html', context)


def feedback_thanks(request):
    return render(request, 'plants/feedback_thanks.html')


def get_filtered_collections(request, species_id):
    """
    Returns a JSON response with filtered collections based on the species_id.

    Used for AJAX requests to dynamically populate options in a form field of BloomEvent admin Snippet.
    """
    # Filter collections to those that match the given species_id
    options = Collection.objects.filter(species=species_id).values('id', 'plant_id')
    return JsonResponse({'options': [{'value': o['id'], 'label': o['plant_id']} for o in options]})
