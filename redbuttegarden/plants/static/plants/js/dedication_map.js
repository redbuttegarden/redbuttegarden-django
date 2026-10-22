const dedicationTokenElement = document.getElementById("mapboxToken");
const dedicationResultsElement = document.getElementById("dedication-results");
const dedicationToken = dedicationTokenElement
    ? JSON.parse(dedicationTokenElement.textContent)
    : null;

if (dedicationToken && window.mapboxgl) {
    mapboxgl.accessToken = dedicationToken;
    const dedicationMap = new mapboxgl.Map({
        container: "dedication-map",
        style: "mapbox://styles/auslaner/ckok8ssno01wy18qubvcflh7x",
        center: [-111.823807, 40.766367],
        zoom: 15,
    });
    const endpoint = new URL("/plants/api/dedications-geojson/", window.location.origin);
    endpoint.search = window.location.search;

    fetch(endpoint)
        .then((response) => response.ok ? response.json() : Promise.reject(response))
        .then((data) => {
            const features = data.features || [];
            if (dedicationResultsElement) {
                dedicationResultsElement.textContent = `${features.length} dedication${features.length === 1 ? "" : "s"} shown.`;
            }
            features.forEach((feature) => {
                const properties = feature.properties || {};
                const coordinates = feature.geometry && feature.geometry.coordinates;
                if (!Array.isArray(coordinates) || coordinates.length < 2) return;
                const popupContent = document.createElement("a");
                popupContent.href = properties.detail_url || "#";
                popupContent.textContent = properties.honoree || properties.garden_name || "View dedication";
                new mapboxgl.Marker()
                    .setLngLat(coordinates)
                    .setPopup(new mapboxgl.Popup().setDOMContent(popupContent))
                    .addTo(dedicationMap);
            });
        })
        .catch(() => {
            if (dedicationResultsElement) dedicationResultsElement.textContent = "Unable to load dedications.";
        });
} else if (dedicationResultsElement) {
    dedicationResultsElement.textContent = "The dedication map is currently unavailable.";
}
