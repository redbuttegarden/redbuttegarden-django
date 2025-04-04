from .models import ConcertDonorClubMember

def concert_donor_club_member(request):
    if request.user.is_authenticated:
        is_concert_donor_club_member = ConcertDonorClubMember.objects.filter(user=request.user).exists()
    else:
        is_concert_donor_club_member = False
    return {'is_concert_donor_club_member': is_concert_donor_club_member}