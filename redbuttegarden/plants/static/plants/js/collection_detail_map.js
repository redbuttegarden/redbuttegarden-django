const mapboxToken = JSON.parse(document.getElementById('mapboxToken').textContent);
let coords = document.getElementById("coords");
let coordText = coords.innerHTML;
let coordinates = coordText.split(", ");

mapboxgl.accessToken = mapboxToken;
const map = new mapboxgl.Map({
    container: 'map', // container ID
    style: 'mapbox://styles/auslaner/ckok8ssno01wy18qubvcflh7x', // style URL
    center: [coordinates[1], coordinates[0]], // starting position [lng, lat]
    zoom: 17 // starting zoom
});

const collectionMarker = new mapboxgl.Marker()
    .setLngLat([coordinates[1], coordinates[0]])
    .addTo(map);