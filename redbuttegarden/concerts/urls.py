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
    path('cdc-tickets/<int:concert_pk>/', views.ticket_detail_view, name='cdc-tickets'),
    path('api/cc-login/', views.cc_login, name='cc-login'),
    path('api/callback/', views.callback, name='callback'),
    path('api/cdc-etix-data/', views.process_ticket_data, name='api-cdc-etix-data'),
    path('api/check-img/', views.check_image_url, name='check-img'),
    path('api/', include(router.urls)),
]
