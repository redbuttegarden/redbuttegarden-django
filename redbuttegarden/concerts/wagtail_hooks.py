from wagtail import hooks

from .views import ConcertDonorClubViewSetGroup


@hooks.register('register_admin_viewset')
def register_viewset():
    return ConcertDonorClubViewSetGroup()
