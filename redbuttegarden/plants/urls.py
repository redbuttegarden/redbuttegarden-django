from django.urls import path, include
from rest_framework.routers import DefaultRouter
from plants import views

router = DefaultRouter()
router.register(r'families', views.FamilyViewSet)
router.register(r'genera', views.GenusViewSet)

app_name = 'plants'
urlpatterns = [
    path('collections/',
         views.CollectionList.as_view(),
         name='collection-list'),
    path('collections/<int:pk>/',
         views.CollectionDetail.as_view(),
         name='collection-detail'),
    path('species/<int:pk>/',
         views.SpeciesDetail.as_view(),
         name='species-detail'),
    path('', include(router.urls)),
]
