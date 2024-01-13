import datetime
import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import viewsets
from wagtail.admin.viewsets.model import ModelViewSet

from concerts.models import Concert, ConcertDonorClubPackage, ConcertDonorClubMember
from concerts.serializers import ConcertSerializer, ConcertDonorClubPackageSerializer, ConcertDonorClubMemberSerializer

logger = logging.getLogger(__name__)


class ConcertDRFViewSet(viewsets.ModelViewSet):
    queryset = Concert.objects.all()
    serializer_class = ConcertSerializer


class ConcertViewSet(ModelViewSet):
    model = Concert
    add_to_admin_menu = True
    inspect_view_enabled = True


class ConcertDonorClubPackageDRFViewSet(viewsets.ModelViewSet):
    queryset = ConcertDonorClubPackage.objects.all()
    serializer_class = ConcertDonorClubPackageSerializer


class ConcertDonorClubPackageViewSet(ModelViewSet):
    model = ConcertDonorClubPackage
    add_to_admin_menu = True
    inspect_view_enabled = True


class ConcertDonorClubMemberDRFViewSet(viewsets.ModelViewSet):
    queryset = ConcertDonorClubMember.objects.all()
    serializer_class = ConcertDonorClubMemberSerializer


class ConcertDonorClubMemberViewSet(ModelViewSet):
    model = ConcertDonorClubMember
    add_to_admin_menu = True
    inspect_view_enabled = True


def concert_thank_you(request):
    referer = request.META.get('HTTP_REFERER')
    logger.debug(f'Referer: {referer}')
    logger.debug(f'HTTP META Dictionary: {request.META}')
    if referer and 'etix.com' in referer:
        return render(request, 'concerts/concert_thank_you.html')
    else:
        return redirect('/')


@login_required
def concert_donor_club_member_profile(request):
    """
    Concert Donor Club member profile to display CDC package details &
    concert itinerary.
    """
    concert_donor_club_member = get_object_or_404(ConcertDonorClubMember, pk=request.user.id)

    current_year = datetime.date.today().year

    current_season_package = concert_donor_club_member.packages.filter(year=current_year)
    current_season_additional_concerts = concert_donor_club_member.additional_concerts.filter(year=current_year)
    return render(request, 'concerts/concert_donor_club_member.html',
                  {'cdc_member': concert_donor_club_member, 'package': current_season_package,
                   'add_concerts': current_season_additional_concerts})
