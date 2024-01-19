import datetime
import logging

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect
from rest_framework import viewsets
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
    form_fields = ['name', 'year']
    inspect_view_enabled = True


class ConcertDonorClubPackageDRFViewSet(viewsets.ModelViewSet):
    queryset = ConcertDonorClubPackage.objects.all()
    serializer_class = ConcertDonorClubPackageSerializer


class ConcertDonorClubPackageViewSet(ModelViewSet):
    model = ConcertDonorClubPackage
    form_fields = ['name', 'year', 'concerts']
    inspect_view_enabled = True


class ConcertDonorClubMemberDRFViewSet(viewsets.ModelViewSet):
    queryset = ConcertDonorClubMember.objects.all()
    serializer_class = ConcertDonorClubMemberSerializer


class ConcertDonorClubMemberViewSet(ModelViewSet):
    model = ConcertDonorClubMember
    form_fields = ['user', 'phone_number', 'packages', 'additional_concerts']
    inspect_view_enabled = True


class TicketDRFViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer()


class TicketViewSet(ModelViewSet):
    model = Ticket
    form_fields = ['owner', 'concert', 'serial']


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
        return JsonResponse({'status': 'failure'})

    if Token.objects.filter(key=token).exists():
        data = json.loads(request.data)
        return JsonResponse({'status': 'success', 'data': data})

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

    current_season_packages = concert_donor_club_member.packages.filter(year=current_year)
    current_season_additional_concerts = concert_donor_club_member.additional_concerts.filter(year=current_year)
    context = {
        'user_name': request.user.get_full_name(),
        'cdc_member': concert_donor_club_member,
        # I expect there will almost always only be one package per member but may as well support multiple
        'packages': current_season_packages,
        'add_concerts': current_season_additional_concerts
    }
    return render(request, 'concerts/concert_donor_club_member.html', context)
