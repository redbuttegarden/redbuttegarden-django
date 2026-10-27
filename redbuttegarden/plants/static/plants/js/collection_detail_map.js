window.initializeMapboxMap = function initializeCollectionDetailMap() {
const tokenElement = document.getElementById('mapboxToken');
const coords = document.getElementById("coords");
const mapContainer = document.getElementById("map");
if (!tokenElement || !coords || !mapContainer) {
    throw new Error("Map details are unavailable.");
}
const mapboxToken = JSON.parse(tokenElement.textContent);
const coordinates = coords.textContent.split(", ");

if (!mapboxToken || coordinates.length !== 2 || coordinates.some((value) => !Number.isFinite(Number(value)))) {
    throw new Error("Map details are unavailable.");
}

mapboxgl.accessToken = mapboxToken;
const map = new mapboxgl.Map({
    container: mapContainer,
    style: 'mapbox://styles/auslaner/ckok8ssno01wy18qubvcflh7x', // style URL
    center: [coordinates[1], coordinates[0]], // starting position [lng, lat]
    zoom: 17 // starting zoom
});

const collectionMarker = new mapboxgl.Marker()
    .setLngLat([coordinates[1], coordinates[0]])
    .addTo(map);
return map;
};
