from django.urls import path, include
from rest_framework.routers import DefaultRouter

from plants import views

router = DefaultRouter()
router.register(r'families', views.FamilyViewSet)
router.register(r'genera', views.GenusViewSet)
router.register(r'locations', views.LocationViewSet)

app_name = 'plants'
urlpatterns = [
    path('api/token/',
         views.CustomAuthToken.as_view(),
         name='api-token'),
    path('api/collections/',
         views.CollectionList.as_view(),
         name='api-collection-list'),
    path('api/collections/<int:pk>/',
         views.CollectionDetail.as_view(),
         name='api-collection-detail'),
    path('api/species/',
         views.SpeciesList.as_view(),
         name='api-species-list'),
    path('api/species/<int:pk>/',
         views.SpeciesDetail.as_view(),
         name='api-species-detail'),
    path('api/species/<int:pk>/set-image/',
         views.set_image,
         name='api-set-species-image'),
    path('collection/<int:collection_id>/',
         views.collection_detail,
         name='collection-detail'),
    path('species/<int:species_id>/',
         views.species_detail,
         name='species-detail'),
    path('plant-map/',
         views.plant_map_view,
         name='plant-map'),
    path('search/',
         views.collection_search,
         name='collection-search'),
    path('collection-list/',
         views.collection_list,
         name='collection-list'),
    path('species-feedback/<int:species_id>/',
         views.species_or_collection_feedback,
         name='species-feedback'),
    path('collection-feedback/<int:collection_id>/',
         views.species_or_collection_feedback,
         name='collection-feedback'),
    path('thanks/',
         views.feedback_thanks,
         name='feedback-thanks'),
    path('', include(router.urls)),
]
