from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from plants import views

urlpatterns = format_suffix_patterns([
    path('collections/',
         views.CollectionList.as_view(),
         name='collection-list'),
    path('collections/<int:pk>/',
         views.CollectionDetail.as_view(),
         name='collection-detail'),
    path('family/<int:pk>/',
         views.FamilyDetail.as_view(),
         name='family-detail'),
    path('species/<int:pk>/',
         views.SpeciesDetail.as_view(),
         name='species-detail')
])
