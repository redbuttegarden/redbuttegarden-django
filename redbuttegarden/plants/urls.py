from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from plants import views

urlpatterns = format_suffix_patterns([
    path('collections/', views.collection_list),
    path('collections/<int:pk>/', views.collection_detail),
    path('family/<int:pk>/',
         views.FamilyDetail.as_view(),
         name='family-detail'),
    path('species/<int:pk>/',
         views.SpeciesDetail.as_view(),
         name='species-detail')
])
