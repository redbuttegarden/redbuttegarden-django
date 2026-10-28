from django.urls import path, include
from rest_framework.routers import DefaultRouter

from plants import views
from plants.feeds import GardenBloomFeed, GardenBloomICalFeed

router = DefaultRouter()
router.register(r"families", views.FamilyViewSet)
router.register(r"genera", views.GenusViewSet)
router.register(r"locations", views.LocationViewSet)

app_name = "plants"
urlpatterns = [
    path("api/token/", views.CustomAuthToken.as_view(), name="api-token"),
    path(
        "api/collections/", views.CollectionList.as_view(), name="api-collection-list"
    ),
    path(
        "api/collections/<int:pk>/",
        views.CollectionDetail.as_view(),
        name="api-collection-detail",
    ),
    path(
        "api/collections/bulk/",
        views.bulk_collections,
        name="api-collections-bulk",
    ),
    path("api/species/", views.SpeciesList.as_view(), name="api-species-list"),
    path(
        "api/species/<int:pk>/",
        views.SpeciesDetail.as_view(),
        name="api-species-detail",
    ),
    path(
        "api/species/<int:pk>/set-image/",
        views.set_species_image,
        name="api-set-species-image",
    ),
    path(
        "api/plants/<str:plant_id>/set-image/",
        views.set_plant_image,
        name="api-set-plant-image",
    ),
    path("api/images/bulk/", views.bulk_images, name="api-images-bulk"),
    path(
        "api/images/direct-upload/initiate/",
        views.initiate_direct_upload,
        name="api-direct-upload-initiate",
    ),
    path(
        "api/images/direct-upload/finalize/",
        views.finalize_direct_upload,
        name="api-direct-upload-finalize",
    ),
    path("species-images/", views.SpeciesImageListView.as_view(), name="speciesimage-list"),
    path(
        "api/species-images/<int:pk>/image-description/",
        views.SpeciesImageEditImageDescriptionView.as_view(),
        name="speciesimage-image-description",
    ),
    path(
        "api/collections-geojson/",
        views.collections_geojson,
        name="api-collections-geojson",
    ),
    path("api/get-garden-code/", views.get_garden_code_view, name="get-garden-code"),
    path(
        "collection/<int:collection_id>/",
        views.collection_detail,
        name="collection-detail",
    ),
    path(
        "dedication/<int:collection_id>/",
        views.dedication_detail,
        name="dedication-detail",
    ),
    path("species/<int:species_id>/", views.species_detail, name="species-detail"),
    path(
        "species/<int:species_id>/preview/",
        views.species_preview,
        name="species-preview",
    ),
    path("plant-map/", views.plant_map_view, name="plant-map"),
    path("dedication-map/", views.dedication_map_view, name="dedication-map"),
    path(
        "api/dedications-geojson/",
        views.dedications_geojson,
        name="api-dedications-geojson",
    ),
    path("collections/results/", views.collection_results, name="collection-results"),
    path("collections/search/", views.collection_search_page, name="collection-search"),
    path(
        "species-feedback/<int:species_id>/",
        views.species_or_collection_feedback,
        name="species-feedback",
    ),
    path(
        "collection-feedback/<int:collection_id>/",
        views.species_or_collection_feedback,
        name="collection-feedback",
    ),
    path("thanks/", views.feedback_thanks, name="feedback-thanks"),
    path("top-trees/", views.top_trees, name="top-trees"),
    path(
        "admin/snippets/filtered_collections/<int:species_id>/",
        views.get_filtered_collections,
        name="get_filtered_collections",
    ),
    path("rss/", GardenBloomFeed(), name="bloom-rss"),
    path("ical/", GardenBloomICalFeed(), name="bloom-ical"),
    path("", include(router.urls)),
]
