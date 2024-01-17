from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'concerts', views.ConcertDRFViewSet)
router.register(r'cdc-packages', views.ConcertDonorClubPackageDRFViewSet)
router.register(r'cdc-members', views.ConcertDonorClubMemberDRFViewSet)
router.register(r'cdc-tickets', views.TicketDRFViewSet)

app_name = 'concerts'
urlpatterns = [
    path('thank-you/', views.concert_thank_you, name='thank-you'),
    path('cdc-member-profile/', views.concert_donor_club_member_profile, name='cdc-profile'),
    path('api/', include(router.urls)),
]
