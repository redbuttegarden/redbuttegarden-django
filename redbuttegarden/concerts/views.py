import datetime
import logging
from urllib.parse import urlparse

from authlib.integrations.base_client import OAuthError
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db.models import Count
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from urllib3 import HTTPResponse
from wagtail.admin.viewsets.base import ViewSetGroup
from wagtail.admin.viewsets.model import ModelViewSet

from concerts.models import Concert, ConcertDonorClubPackage, ConcertDonorClubMember, Ticket, OAuth2Token
from concerts.serializers import ConcertSerializer, ConcertDonorClubPackageSerializer, ConcertDonorClubMemberSerializer, \
    TicketSerializer
from concerts.utils.constant_contact import oauth

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


class ConcertDonorClubMemberDRFViewSet(viewsets.ModelViewSet):
    queryset = ConcertDonorClubMember.objects.all()
    serializer_class = ConcertDonorClubMemberSerializer


class ConcertDonorClubMemberViewSet(ModelViewSet):
    model = ConcertDonorClubMember
    form_fields = '__all__'
    icon = 'group'
    inspect_view_enabled = True


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
    items = (ConcertViewSet, ConcertDonorClubPackageViewSet, ConcertDonorClubMemberViewSet, TicketViewSet)


def concert_thank_you(request):
    referer = request.META.get('HTTP_REFERER')
    if referer:
        parsed_url = urlparse(referer)
        if parsed_url.hostname == 'etix.com' or parsed_url.hostname == 'www.etix.com':
            return render(request, 'concerts/concert_thank_you.html')
        else:
            return HTTPResponse(status=204)
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
    """
    try:
        concert_donor_club_member = ConcertDonorClubMember.objects.get(user=request.user)
    except ConcertDonorClubMember.DoesNotExist:
        raise Http404("No matching Concert Donor Membership found.")

    current_year = datetime.date.today().year

    current_season_packages = concert_donor_club_member.packages.annotate(num_concerts=Count("concerts")).filter(
        num_concerts__gt=0, year=current_year)
    current_season_member_tickets = Ticket.objects.filter(owner=concert_donor_club_member,
                                                          concert__begin__year=current_year, package__isnull=False)
    current_season_additional_concert_tickets = Ticket.objects.filter(owner=concert_donor_club_member,
                                                                      concert__begin__year=current_year,
                                                                      package__isnull=True)

    ticket_info = {}
    for package in current_season_packages:
        ticket_info[package.name] = []
        for concert in package.concerts.all():
            ticket_count = current_season_member_tickets.filter(concert=concert).count()

            if ticket_count > 0:
                ticket_info[package.name].append({
                    'concert_pk': concert.pk,
                    'name': concert.name,
                    'begin': concert.begin,
                    'doors': concert.begin - datetime.timedelta(
                        minutes=concert.doors_before_event_time_minutes),
                    'img_url': concert.image_url,
                    'count': ticket_count
                })

    add_ticket_info = {}
    for ticket in current_season_additional_concert_tickets:
        ticket_count = current_season_additional_concert_tickets.filter(concert=ticket.concert).count()

        if ticket_count > 0:
            add_ticket_info[ticket.concert.etix_id] = {
                'concert_pk': ticket.concert.pk,
                'name': ticket.concert.name,
                'begin': ticket.concert.begin,
                'doors': ticket.concert.begin - datetime.timedelta(
                    minutes=ticket.concert.doors_before_event_time_minutes),
                'img_url': ticket.concert.image_url,
                'count': ticket_count
            }

    context = {
        'user_name': request.user.get_full_name(),
        'cdc_member': concert_donor_club_member,
        # I expect there will almost always only be one package per member but may as well support multiple
        'ticket_info': ticket_info,
        'add_ticket_info': add_ticket_info,
        'member_tickets': current_season_member_tickets,
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

