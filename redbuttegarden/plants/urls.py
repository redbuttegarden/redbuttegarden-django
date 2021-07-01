from django.urls import path, include
from rest_framework.routers import DefaultRouter
from plants import views

router = DefaultRouter()
router.register(r'families', views.FamilyViewSet)
router.register(r'genera', views.GenusViewSet)
router.register(r'locations', views.LocationViewSet)

app_name = 'plants'
urlpatterns = [
    path('collections/',
         views.CollectionList.as_view(),
         name='collection-list'),
    path('collections/<int:pk>/',
         views.CollectionDetail.as_view(),
         name='collection-detail'),
    path('species/',
         views.SpeciesList.as_view(),
         name='species-list'),
    path('species/<int:pk>/',
         views.SpeciesDetail.as_view(),
         name='species-detail'),
    path('plant-map/',
         views.plant_map_view,
         name='plant-map'),
    path('', include(router.urls)),
]
