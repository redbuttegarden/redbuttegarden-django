window.initializeMapboxMap = function initializeDedicationDetailMap() {
const tokenElement = document.getElementById("mapboxToken");
const coordinatesElement = document.getElementById("dedication-coordinates");
const mapContainer = document.getElementById("dedication-map");

const token = tokenElement ? JSON.parse(tokenElement.textContent) : null;

if (token && coordinatesElement && mapContainer && window.mapboxgl) {
    mapboxgl.accessToken = token;
    const latitude = Number(coordinatesElement.dataset.latitude);
    const longitude = Number(coordinatesElement.dataset.longitude);

    if (Number.isFinite(latitude) && Number.isFinite(longitude)) {
        const map = new mapboxgl.Map({
            container: mapContainer,
            style: "mapbox://styles/auslaner/ckok8ssno01wy18qubvcflh7x",
            center: [longitude, latitude],
            zoom: 17,
        });
        new mapboxgl.Marker().setLngLat([longitude, latitude]).addTo(map);
        return map;
    } else {
        throw new Error("Map details are unavailable.");
    }
} else {
    throw new Error("Map details are unavailable.");
}
};
