import datetime
import logging
import requests
from urllib.parse import urlparse

from authlib.integrations.base_client import OAuthError
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db.models import Count
from django.http import Http404, JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django_filters.rest_framework import FilterSet, CharFilter
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from wagtail.admin.viewsets.base import ViewSetGroup
from wagtail.admin.viewsets.model import ModelViewSet

from concerts.forms import ConcertDonorClubPackageForm
from concerts.models import Concert, ConcertDonorClubPackage, ConcertDonorClubMember, Ticket, OAuth2Token, \
    ConcertDonorClubMemberGroup
from concerts.serializers import ConcertSerializer, ConcertDonorClubPackageSerializer, ConcertDonorClubMemberSerializer, \
    TicketSerializer
from concerts.utils.constant_contact import oauth
from concerts.utils.cdc_view_utils import summarize_tickets

logger = logging.getLogger(__name__)


def cc_login(request):
    # build a full authorize callback uri
    redirect_uri = request.build_absolute_uri(reverse('concerts:callback'))
    logger.debug(redirect_uri)
    return oauth.constant_contact.authorize_redirect(request, redirect_uri)


def callback(request):
    try:
        token = oauth.constant_contact.authorize_access_token(request)
    except OAuthError as e:
        logger.error(f'OAuthError during token callback: {e}')
        messages.add_message(request, messages.ERROR, 'Failed to authenticate with Constant Contact.')
        return redirect('/')

    OAuth2Token.objects.update_or_create(
        user=request.user,
        name='constant_contact',
        defaults={
            'token_type': token['token_type'],
            'access_token': token['access_token'],
            'refresh_token': token['refresh_token'],
            'expires_at': token['expires_at'],
        }
    )
    messages.add_message(request, messages.SUCCESS, 'Successfully authenticated with Constant Contact.')
    return redirect('/')


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'page_size'
    max_page_size = 10000


class ConcertDRFViewSet(viewsets.ModelViewSet):
    queryset = Concert.objects.all()
    serializer_class = ConcertSerializer


class ConcertViewSet(ModelViewSet):
    model = Concert
    form_fields = '__all__'
    icon = 'media'
    inspect_view_enabled = True


class ConcertDonorClubPackageDRFViewSet(viewsets.ModelViewSet):
    queryset = ConcertDonorClubPackage.objects.all()
    serializer_class = ConcertDonorClubPackageSerializer


class ConcertDonorClubPackageViewSet(ModelViewSet):
    model = ConcertDonorClubPackage
    form_fields = '__all__'
    icon = 'list-ul'
    inspect_view_enabled = True

    def get_form_class(self, *args, **kwargs):
        return ConcertDonorClubPackageForm


class ConcertDonorClubMemberFilter(FilterSet):
    email = CharFilter(field_name='user__email', lookup_expr='iexact')
    username = CharFilter(field_name='user__username', lookup_expr='iexact')

    class Meta:
        fields = ('email', 'username')
        model = ConcertDonorClubMember


class ConcertDonorClubMemberDRFViewSet(viewsets.ModelViewSet):
    queryset = ConcertDonorClubMember.objects.all()
    serializer_class = ConcertDonorClubMemberSerializer
    filterset_class = ConcertDonorClubMemberFilter


class ConcertDonorClubMemberViewSet(ModelViewSet):
    model = ConcertDonorClubMember
    form_fields = '__all__'
    icon = 'user'
    inspect_view_enabled = True
    search_fields = ('user__email', 'user__username', 'user__first_name', 'user__last_name')
    list_filter = ('active', 'packages')


class ConcertDonorClubMemberGroupViewSet(ModelViewSet):
    model = ConcertDonorClubMemberGroup
    form_fields = '__all__'
    icon = 'group'
    inspect_view_enabled = True
    search_fields = ('id', 'members_user__email', 'members_user__username')
    list_filter = ['id']


class TicketDRFViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    pagination_class = LargeResultsSetPagination


class TicketViewSet(ModelViewSet):
    model = Ticket
    form_fields = '__all__'
    icon = 'tag'
    list_filter = ('owner', 'concert', 'package', 'order_id', 'barcode')


class ConcertDonorClubViewSetGroup(ViewSetGroup):
    menu_label = 'Concert Donor Club'
    menu_icon = 'group'
    items = (ConcertViewSet, ConcertDonorClubPackageViewSet, ConcertDonorClubMemberViewSet, TicketViewSet,
             ConcertDonorClubMemberGroupViewSet)


def concert_thank_you(request):
    referer = request.META.get('HTTP_REFERER')
    if referer:
        parsed_url = urlparse(referer)
        if parsed_url.hostname == 'etix.com' or parsed_url.hostname == 'www.etix.com':
            return render(request, 'concerts/concert_thank_you.html')
        else:
            return HttpResponse(status=204)
    else:
        return redirect('/')


@api_view(['POST'])
def process_ticket_data(request):
    # Check if user has a valid API Token
    try:
        token = request.META['HTTP_AUTHORIZATION'].split(' ')[1]
    except KeyError:
        return JsonResponse({'status': 'Auth failure'})

    if Token.objects.filter(key=token).exists():
        logger.info(f'Incoming ticket request data: {request.data}')

        if not request.data['event_name']:
            return JsonResponse({'status': 'Failure', 'msg': 'Event name required.'})

        """
        We can't use update_or_create for Concerts because some incoming data may be less complete than others
        and we don't want to overwrite existing data with null values. This issue seems most prevalent for the image_url
        """
        concert_defaults = {
            'etix_id': request.data['event_id'],
            'name': request.data['event_name'],
            'begin': datetime.datetime.fromisoformat(request.data['event_begin'].replace("Z", "+00:00")),
            'end': datetime.datetime.fromisoformat(request.data['event_end'].replace("Z", "+00:00")),
            'doors_before_event_time_minutes': int(request.data['event_doors_before_event_time_minutes']),
            'image_url': request.data['event_image_url'],
        }
        try:
            concert = Concert.objects.get(etix_id=request.data['event_id'])
            for key, value in concert_defaults.items():
                if value:
                    setattr(concert, key, value)
                concert.save()
        except Concert.DoesNotExist:
            concert = Concert.objects.create(etix_id=request.data['event_id'],
                                             name=request.data['event_name'],
                                             begin=datetime.datetime.fromisoformat(
                                                 request.data['event_begin'].replace("Z", "+00:00")),
                                             end=datetime.datetime.fromisoformat(
                                                 request.data['event_end'].replace("Z", "+00:00")),
                                             doors_before_event_time_minutes=int(
                                                 request.data['event_doors_before_event_time_minutes']),
                                             image_url=request.data['event_image_url'])

            logger.info(f'Concert Donor Club Concert created: {concert}')

        cdc_user, created = get_user_model().objects.update_or_create(username=request.data['etix_username'],
                                                                      defaults={
                                                                          'email': request.data['owner_email'],
                                                                          'first_name': request.data[
                                                                              'owner_first_name'] if request.data[
                                                                                                         'owner_first_name'] != '*' else '',
                                                                          'last_name': request.data[
                                                                              'owner_last_name']})

        if created:
            logger.debug(f'Created user {cdc_user}. Adding them to CDC member group...')
            cdc_user.groups.add(Group.objects.get(name="Concert Donor Club Member"))

        cdc_member, created = ConcertDonorClubMember.objects.update_or_create(user=cdc_user, defaults={
            'phone_number': request.data['owner_phone']})

        if created:
            logger.debug(f'Created ConcertDonorClubMember {cdc_member}')

        package = None
        if request.data['package_name'].strip():
            package, package_created = ConcertDonorClubPackage.objects.get_or_create(name=request.data['package_name'],
                                                                                     defaults={
                                                                                         'year': datetime.datetime.now().year})

            if package_created:
                logger.debug(f'Concert Donor Club Package created: {package}')

        ticket, ticket_created = Ticket.objects.update_or_create(barcode=request.data['ticket_barcode'],
                                                                 defaults={
                                                                     'order_id': request.data['order_id'],
                                                                     'owner': cdc_member,
                                                                     'concert': concert,
                                                                     'package': package,
                                                                 })
        if package:
            cdc_member.packages.add(package)

        serialized_ticket = TicketSerializer(ticket).data

        return JsonResponse({'status': 'success', 'ticket': serialized_ticket, 'created': ticket_created})

    return JsonResponse({'status': 'Auth failure'})


@login_required
def concert_donor_club_member_profile(request):
    """
    Concert Donor Club member profile to display CDC package details &
    concert itinerary.

    We could display individual tickets and earlier iterations did so along with a
    concert detail page but at the moment it was requested to only show
    ticket count totals per package and concert.
    """
    try:
        concert_donor_club_member = ConcertDonorClubMember.objects.get(user=request.user)
    except ConcertDonorClubMember.DoesNotExist:
        raise Http404("No matching Concert Donor Membership found.")

    current_year = datetime.date.today().year

    current_season_packages = concert_donor_club_member.packages.annotate(num_concerts=Count("concerts")).filter(
        num_concerts__gt=0, year=current_year)
    current_season_tickets = Ticket.objects.filter(concert__begin__year=current_year)
    current_season_member_tickets = current_season_tickets.filter(owner=concert_donor_club_member,
                                                                  package__isnull=False)
    current_season_additional_concert_tickets = current_season_tickets.filter(owner=concert_donor_club_member,
                                                                              package__isnull=True)

    # Check if CDC member is part of any Concert Donor Club Member Group
    try:
        cdc_member_group = ConcertDonorClubMemberGroup.objects.filter(members__in=[concert_donor_club_member]).first()
    except ConcertDonorClubMemberGroup.DoesNotExist:
        cdc_member_group = None

    if cdc_member_group:
        other_group_members = [member for member in cdc_member_group.members.all()]
        # Remove the current user from the list of other group members
        other_group_members.remove(concert_donor_club_member)
        # Get all the package tickets for other members in the group
        group_tickets = current_season_tickets.filter(owner__in=[member for member in other_group_members],
                                                      package__isnull=False)
        group_tickets_by_concert = summarize_tickets(group_tickets)
    else:
        other_group_members = []
        group_tickets_by_concert = None

    ticket_info = {}
    for package in current_season_packages:
        ticket_info[package.name] = summarize_tickets(current_season_member_tickets, package.concerts.all())

    add_ticket_info = summarize_tickets(current_season_additional_concert_tickets)

    context = {
        'user_full_name': request.user.get_full_name(),
        'cdc_member': concert_donor_club_member,
        # I expect there will almost always only be one package per member but may as well support multiple
        'ticket_info': ticket_info,
        'add_ticket_info': add_ticket_info,
        'other_group_member_usernames': [member.user.username for member in other_group_members],
        'group_tickets_by_concert': group_tickets_by_concert,
    }
    return render(request, 'concerts/concert_donor_club_member_profile.html', context)


@login_required
def ticket_detail_view(request, concert_pk):
    """
    Display members tickets for given concert
    """
    try:
        concert_donor_club_member = ConcertDonorClubMember.objects.get(user=request.user)
    except ConcertDonorClubMember.DoesNotExist:
        raise Http404("No matching Concert Donor Membership found.")

    concert = Concert.objects.get(pk=concert_pk)

    context = {
        'concert': concert,
        'doors': concert.begin - datetime.timedelta(minutes=concert.doors_before_event_time_minutes),
        'tickets': Ticket.objects.filter(owner=concert_donor_club_member, concert=concert),
    }

    return render(request, 'concerts/concert_donor_club_tickets.html', context)


def check_image_url(request):
    """
    Check if the Etix band image will actually load
    Annoyingly, Etix returns a 200 status code when requesting an image
    url that doesn't load so instead we have to check the header content
    length to check if the image actually exists
    """
    image_url = request.GET.get('image_url')
    concert_name = request.GET.get('concert_name')
    response = requests.head(image_url)

    # HTMX won't swap content if we return 204
    if not 'Content-Length' in response.headers or response.headers['Content-Length'] == '0':
        # Image won't load so replace it with a placeholder that doesn't use an animation
        return HttpResponse(
            '<div class="placeholder w-100 h-100"><div class="placeholder col-12 h-100 w-100 rounded-1"></div></div>')
    else:
        return HttpResponse(
            f'<img class="img-fluid rounded-start" src="{image_url}" alt="Concert promo art for {concert_name}">')
