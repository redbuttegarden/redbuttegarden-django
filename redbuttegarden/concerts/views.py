import datetime
import logging

import code128
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from wagtail.admin.viewsets.base import ViewSetGroup
from wagtail.admin.viewsets.model import ModelViewSet

from concerts.models import Concert, ConcertDonorClubPackage, ConcertDonorClubMember, Ticket
from concerts.serializers import ConcertSerializer, ConcertDonorClubPackageSerializer, ConcertDonorClubMemberSerializer, \
    TicketSerializer

logger = logging.getLogger(__name__)


class ConcertDRFViewSet(viewsets.ModelViewSet):
    queryset = Concert.objects.all()
    serializer_class = ConcertSerializer


class ConcertViewSet(ModelViewSet):
    model = Concert
    form_fields = '__all__'
    inspect_view_enabled = True


class ConcertDonorClubPackageDRFViewSet(viewsets.ModelViewSet):
    queryset = ConcertDonorClubPackage.objects.all()
    serializer_class = ConcertDonorClubPackageSerializer


class ConcertDonorClubPackageViewSet(ModelViewSet):
    model = ConcertDonorClubPackage
    form_fields = '__all__'
    inspect_view_enabled = True


class ConcertDonorClubMemberDRFViewSet(viewsets.ModelViewSet):
    queryset = ConcertDonorClubMember.objects.all()
    serializer_class = ConcertDonorClubMemberSerializer


class ConcertDonorClubMemberViewSet(ModelViewSet):
    model = ConcertDonorClubMember
    form_fields = '__all__'
    inspect_view_enabled = True


class TicketDRFViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer()


class TicketViewSet(ModelViewSet):
    model = Ticket
    form_fields = '__all__'
    list_filter = ('owner', 'concert', 'package', 'order_id', 'barcode')


class ConcertDonorClubViewSetGroup(ViewSetGroup):
    menu_label = 'Concert Donor Club'
    menu_icon = 'group'
    items = (ConcertViewSet, ConcertDonorClubPackageViewSet, ConcertDonorClubMemberViewSet, TicketViewSet)


def concert_thank_you(request):
    referer = request.META.get('HTTP_REFERER')
    logger.debug(f'Referer: {referer}')
    logger.debug(f'HTTP META Dictionary: {request.META}')
    if referer and 'etix.com' in referer:
        return render(request, 'concerts/concert_thank_you.html')
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

        concert, concert_created = Concert.objects.get_or_create(etix_id=request.data['event_id'],
                                                                 defaults={'name': request.data['event_name'],
                                                                           'begin': datetime.datetime.fromisoformat(
                                                                               request.data['event_begin'].replace("Z",
                                                                                                                   "+00:00")),
                                                                           'end': datetime.datetime.fromisoformat(
                                                                               request.data['event_end'].replace("Z",
                                                                                                                 "+00:00")),
                                                                           'doors_before_event_time_minutes': int(
                                                                               request.data[
                                                                                   'event_doors_before_event_time_minutes']),
                                                                           'image_url': request.data[
                                                                               'event_image_url']})
        if concert_created:
            logger.info(f'Concert Donor Club Concert created: {concert}')

        try:
            cdc_member = ConcertDonorClubMember.objects.get(user__username=request.data['etix_username'])
        except ConcertDonorClubMember.DoesNotExist:
            return JsonResponse({'status': 'No matching CDC member found.'})

        package = None
        if request.data['package_name']:
            package, package_created = ConcertDonorClubPackage.objects.get_or_create(name=request.data['package_name'],
                                                                                     defaults={
                                                                                         'year': datetime.datetime.now().year})
            if package_created:
                logger.info(f'Concert Donor Club Package created: {package}')

        if request.data['ticket_status'] in ['ISSUED', 'REDEEMED', 'RESERVED']:
            logger.debug(Ticket.objects.all())
            ticket, ticket_created = Ticket.objects.update_or_create(barcode=request.data['ticket_barcode'],
                                                                     defaults={
                                                                         'order_id': request.data['order_id'],
                                                                         'owner': cdc_member,
                                                                         'concert': concert,
                                                                         'package': package,
                                                                         'status': request.data['ticket_status'],
                                                                     })

            serialized_ticket = TicketSerializer(ticket).data

            return JsonResponse({'status': 'success', 'ticket': serialized_ticket, 'created': ticket_created})

        elif request.data['ticket_status'] == 'VOID':
            try:
                ticket = Ticket.objects.get(owner=cdc_member, barcode=request.data['ticket_barcode'])
            except Ticket.DoesNotExist:
                return JsonResponse({'status': 'unchanged', 'msg': 'No matching Ticket found for given CDC member.'})

            serialized_ticket = TicketSerializer(ticket).data
            ticket.delete()

            return JsonResponse({'status': 'success', 'ticket': serialized_ticket, 'deleted': True})

        else:
            return JsonResponse({'status': f'Ticket status {request.data["ticket_status"]} requires no action'})

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

    current_year = 2023  # TODO - Change back to datetime.date.today().year after testing

    current_season_packages = concert_donor_club_member.packages.filter(year=current_year)
    current_season_additional_concert_tickets = Ticket.objects.filter(owner=concert_donor_club_member,
                                                                      concert__begin__year=current_year)
    member_tickets = Ticket.objects.filter(owner=concert_donor_club_member)

    ticket_info = {}
    for package in current_season_packages:
        ticket_info[package.name] = []
        for concert in package.concerts.all():
            ticket_info[package.name].append({
                'concert_pk': concert.pk,
                'name': concert.name,
                'begin': concert.begin,
                'doors': concert.begin - datetime.timedelta(
                    minutes=concert.doors_before_event_time_minutes),
                'img_url': concert.image_url,
                'count': member_tickets.filter(concert=concert).count()
            })

    add_ticket_info = {}
    for ticket in current_season_additional_concert_tickets:
        add_ticket_info[ticket.concert.etix_id] = {
            'concert_pk': ticket.concert.pk,
            'name': ticket.concert.name,
            'begin': ticket.concert.begin,
            'doors': ticket.concert.begin - datetime.timedelta(minutes=ticket.concert.doors_before_event_time_minutes),
            'img_url': ticket.concert.image_url,
            'count': current_season_additional_concert_tickets.filter(concert=ticket.concert).count()
        }

    context = {
        'user_name': request.user.get_full_name(),
        'cdc_member': concert_donor_club_member,
        # I expect there will almost always only be one package per member but may as well support multiple
        'ticket_info': ticket_info,
        'add_ticket_info': add_ticket_info,
        'member_tickets': member_tickets,
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
