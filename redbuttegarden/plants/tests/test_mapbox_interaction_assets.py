"""Regression coverage for deferred Mapbox asset loading."""

from pathlib import Path

from django.test import SimpleTestCase


PLANTS_ROOT = Path(__file__).resolve().parents[1]
MAPBOX_CDN_URL = "https://api.mapbox.com/mapbox-gl-js/"
MAP_TEMPLATES = (
    "collection_map.html",
    "dedication_map.html",
    "collection_detail.html",
    "dedication_detail.html",
)


class MapboxInteractionAssetTests(SimpleTestCase):
    """Ensure public map templates defer all Mapbox CDN requests."""

    def test_map_templates_use_the_interaction_loader_without_eager_mapbox_assets(self) -> None:
        """Keep passive page loads from fetching Mapbox resources."""

        for template_name in MAP_TEMPLATES:
            with self.subTest(template=template_name):
                template = (
                    PLANTS_ROOT / "templates" / "plants" / template_name
                ).read_text()

                self.assertNotIn(MAPBOX_CDN_URL, template)
                self.assertIn("mapbox_interaction_loader.js", template)
                self.assertIn("data-mapbox-status", template)
                self.assertIn("data-mapbox-container", template)
                self.assertIn("data-mapbox-placeholder", template)
                self.assertIn("map_placeholder.css", template)

    def test_interaction_loader_waits_for_input_and_loads_pinned_assets(self) -> None:
        """Keep the no-friction activation contract and CDN pinning explicit."""

        loader = (
            PLANTS_ROOT / "static" / "plants" / "js" / "mapbox_interaction_loader.js"
        ).read_text()

        self.assertIn(MAPBOX_CDN_URL, loader)
        self.assertIn('document.addEventListener("pointerdown", startMap', loader)
        self.assertIn('document.addEventListener("touchstart", startMap', loader)
        self.assertIn('document.addEventListener("keydown", startMap)', loader)
        self.assertIn("window.initializeMapboxMap()", loader)
        self.assertIn('map.once("error"', loader)
        self.assertIn("await waitForMap(map)", loader)
        self.assertIn("setPlaceholder(false, \"Loading interactive map.\")", loader)
        self.assertIn("Location details remain available on this page.", loader)
