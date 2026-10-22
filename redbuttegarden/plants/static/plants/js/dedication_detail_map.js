const tokenElement = document.getElementById("mapboxToken");
const coordinatesElement = document.getElementById("dedication-coordinates");
const mapStatusElement = document.getElementById("dedication-map-status");

const token = tokenElement ? JSON.parse(tokenElement.textContent) : null;

if (token && coordinatesElement && window.mapboxgl) {
    mapboxgl.accessToken = token;
    const latitude = Number(coordinatesElement.dataset.latitude);
    const longitude = Number(coordinatesElement.dataset.longitude);

    if (Number.isFinite(latitude) && Number.isFinite(longitude)) {
        const map = new mapboxgl.Map({
            container: "dedication-map",
            style: "mapbox://styles/auslaner/ckok8ssno01wy18qubvcflh7x",
            center: [longitude, latitude],
            zoom: 17,
        });
        new mapboxgl.Marker().setLngLat([longitude, latitude]).addTo(map);
    }
} else if (mapStatusElement) {
    mapStatusElement.textContent = "The dedication map is currently unavailable.";
}
