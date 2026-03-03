console.log("plant_map.js loaded");

const mapboxToken = JSON.parse(document.getElementById('mapboxToken').textContent);

mapboxgl.accessToken = mapboxToken;
const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/auslaner/ckrdvnurq2ix018o34dv8sxft',
    center: [-111.823807, 40.766367],
    zoom: 16
});

function isMobile() {
    return /Mobi|Android|iPhone|iPad|iPod|BlackBerry|Windows Phone/i.test(navigator.userAgent);
}

if (isMobile()) {
    const geolocateControl = new mapboxgl.GeolocateControl({
        positionOptions: { enableHighAccuracy: true },
        trackUserLocation: true,
        showUserHeading: true,
    });
    map.addControl(geolocateControl, 'bottom-left');
}

// Code for changing styles based off https://docs.mapbox.com/mapbox-gl-js/example/setstyle/
const layerList = document.getElementById('mapMenu');
const inputs = layerList.getElementsByTagName('input');

for (const input of inputs) {
    input.onclick = (layer) => {
        const layerId = layer.target.id;

        if (layerId !== 'rbg-custom') {
            map.setStyle('mapbox://styles/mapbox/' + layerId);
        }

        map.once('styledata', () => {
            console.log('Initializing map with style: ' + layerId);
            initialMapSetup(map);
        });
    };
}

// Holds visible collection features for filtering
let collections = [];

// Create a popup, but don't add it to the map yet.
let popup = new mapboxgl.Popup({ closeButton: false });

let filterEl = document.getElementById('feature-filter');
let listingEl = document.getElementById('feature-listing');

function renderListings(features) {
    features.sort((a, b) =>
        (a.properties.family_name > b.properties.family_name) ? 1 :
            (a.properties.family_name === b.properties.family_name) ?
                ((a.properties.genus_name > b.properties.genus_name) ? 1 :
                    (a.properties.genus_name === b.properties.genus_name) ?
                        ((a.properties.species_name > b.properties.species_name) ? 1 : -1) : -1) : -1
    );

    let empty = document.createElement('p');
    listingEl.innerHTML = '';

    if (features.length) {
        features.forEach(function (feature) {
            if (!feature.properties.cluster) {
                let prop = feature.properties;
                let collection = document.createElement('a');
                collection.href = "/plants/collection/" + prop.id + "/";
                collection.target = '_blank';
                collection.innerHTML = '<div class="feature-listing">' + prop.family_name + ' ' + style_full_name(prop.species_full_name) + '</div>';
                collection.addEventListener('mouseover', function () {
                    popup
                        .setLngLat(feature.geometry.coordinates)
                        .setHTML(style_full_name(prop.species_full_name))
                        .addTo(map);
                });
                listingEl.appendChild(collection);
            }
        });

        filterEl.parentNode.style.display = 'block';
    } else if (features.length === 0 && filterEl.value !== '') {
        empty.textContent = 'No results found';
        listingEl.appendChild(empty);
    } else {
        empty.textContent = 'Drag the map to populate results';
        listingEl.appendChild(empty);

        filterEl.parentNode.style.display = 'none';

        if (map.getLayer('unclustered-point')) {
            map.setFilter('unclustered-point', ['has', 'id']);
        }
    }
}

function normalize(string) {
    return string.trim().toLowerCase();
}

function getUniqueFeatures(array, comparatorProperty) {
    let existingFeatureKeys = {};
    return array.filter(function (el) {
        if (existingFeatureKeys[el.properties[comparatorProperty]]) {
            return false;
        } else {
            existingFeatureKeys[el.properties[comparatorProperty]] = true;
            return true;
        }
    });
}

function resetMapFilter(map) {
    if (map.getLayer('unclustered-point')) {
        map.setFilter('unclustered-point', ['has', 'id']);
    }
}

// ---------------- URL builder (single source of truth) ----------------
function buildCollectionsGeojsonUrl(map) {
    const url = new URL("/plants/api/collections-geojson/", window.location.origin);

    // Preserve existing filter query params (?family_name=... etc)
    url.search = window.location.search;

    // Add bbox if possible (requires map to be initialized)
    try {
        const b = map.getBounds();
        url.searchParams.set("bbox", [
            b.getWest(),
            b.getSouth(),
            b.getEast(),
            b.getNorth(),
        ].join(","));
    } catch (e) {
        // If bounds aren't available yet, just omit bbox
    }

    return url;
}

// ---------- Guards / helpers ----------
let handlersBound = false;

function safeAddImage(map, name, url) {
    if (map.hasImage(name)) return;

    map.loadImage(url, function (error, image) {
        if (error) {
            console.error(`Failed to load image ${name} from ${url}`, error);
            return;
        }
        if (!map.hasImage(name)) {
            map.addImage(name, image);
        }
    });
}

function ensureCollectionsSource(map, featureCollection) {
    const existing = map.getSource('collections');
    if (existing) {
        existing.setData(featureCollection);
        return;
    }

    map.addSource('collections', {
        type: 'geojson',
        data: featureCollection,
        cluster: true,
        clusterMaxZoom: 17,
        clusterRadius: 40,
    });
}

function ensureLayer(map, layerDef) {
    if (map.getLayer(layerDef.id)) return;
    map.addLayer(layerDef);
}

function hideLoader() {
    const el = document.getElementById("map-load-overlay");
    if (el) el.style.display = "none";
}

// Keep these as top-level helpers (used by click handler)
function formatSpeciesFullName(species_id, species_full_name) {
    if (species_id) {
        return '<span class="pop-up-label">Full Name: </span><a href="/plants/species/' + species_id + '/"' + style_full_name(species_full_name) + '</a>';
    } else {
        return '<span class="pop-up-label">Full Name: </span>' + style_full_name(species_full_name);
    }
}

async function refreshCollectionsData(map) {
    const source = map.getSource("collections");
    if (!source) return;

    const url = buildCollectionsGeojsonUrl(map);
    console.log("Refreshing collections from:", url.toString());

    try {
        const response = await fetch(url.toString(), {
            headers: { "Accept": "application/json" },
        });

        if (!response.ok) {
            const text = await response.text().catch(() => "");
            throw new Error(`GeoJSON HTTP ${response.status}. Body starts: ${text.slice(0, 200)}`);
        }

        const featureCollection = await response.json();
        source.setData(featureCollection);
    } catch (err) {
        console.error("Failed to refresh collections:", err);
    }
}

// Bind event handlers once (NOT inside re-run setup)
function bindHandlersOnce(map) {
    if (handlersBound) return;
    handlersBound = true;

    map.on('movestart', function () {
        resetMapFilter(map);
    });

    map.on('moveend', async function () {
        // Keep sidebar updated
        const layers = [];
        if (map.getLayer('clusters')) layers.push('clusters');
        if (map.getLayer('unclustered-point')) layers.push('unclustered-point');
        if (!layers.length) return;

        let features = map.queryRenderedFeatures({ layers });
        if (features) {
            let uniqueFeatures = getUniqueFeatures(features, 'id');
            renderListings(uniqueFeatures);
            collections = uniqueFeatures;
        }

        // Optional but recommended: refresh GeoJSON based on new bbox
        await refreshCollectionsData(map);
    });

    map.on('click', 'clusters', function (e) {
        const source = map.getSource('collections');
        if (!source) return;

        const features = map.queryRenderedFeatures(e.point, { layers: ['clusters'] });
        if (!features || !features.length) return;

        const clusterId = features[0].properties.cluster_id;
        source.getClusterExpansionZoom(clusterId, function (err, zoom) {
            if (err) return;
            map.easeTo({ center: features[0].geometry.coordinates, zoom: zoom });
        });
    });

    map.on('click', 'unclustered-point', function (e) {
        if (!e.features || !e.features.length) return;

        const f = e.features[0];
        const coordinates = f.geometry.coordinates.slice();

        const family_name = f.properties.family_name;
        const genus_name = f.properties.genus_name;
        const species_name = f.properties.species_name;
        const species_full_name = f.properties.species_full_name;
        const species_id = f.properties.species_id;
        const collection_id = f.properties.id;
        const vernacular_name = f.properties.vernacular_name;
        const habit = f.properties.habit;
        const hardiness = f.properties.hardiness;
        const water_regime = f.properties.water_regime;
        const exposure = f.properties.exposure;
        const bloom_time = f.properties.bloom_time;
        const plant_size = f.properties.plant_size;
        const garden_area = f.properties.garden_area;
        const garden_name = f.properties.garden_name;
        const garden_code = f.properties.garden_code;
        const planted_on = f.properties.planted_on;

        function displayList(value) {
            if (!value) return "";

            try {
                const arr = Array.isArray(value) ? value : JSON.parse(value);
                if (Array.isArray(arr)) return arr.join(", ");
            } catch {
                if (typeof value === "string") {
                    return value
                        .split(",")
                        .map(s => s.trim())
                        .filter(Boolean)
                        .join(", ");
                }
            }
            return "";
        }

        const hardinessDisplay = displayList(hardiness);   // "5, 6, 7, 8, 9"
        const bloomTimeDisplay = displayList(bloom_time);  // "April, May"

        const formatted_species_full_name = formatSpeciesFullName(species_id, species_full_name);

        while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
            coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
        }

        new mapboxgl.Popup()
            .setLngLat(coordinates)
            .setHTML(
                '<div class="pop-up-row">' +
                '<a href="/plants/collection/' + collection_id + '/">Collection Detail Page</a>' +
                '</div>' +
                '<div class="pop-up-row"><span class="pop-up-label">Family Name: </span>' + family_name + '</div>' +
                '<div class="pop-up-row"><span class="pop-up-label">Genus Name: </span><span class="scientific-name">' + genus_name + '</span></div>' +
                '<div class="pop-up-row"><span class="pop-up-label">Species Name: </span><span class="scientific-name">' + species_name + '</span></div>' +
                '<div class="pop-up-row">' + formatted_species_full_name + '</div>' +
                '<div class="pop-up-row"><span class="pop-up-label">Vernacular Name: </span>' + vernacular_name + '</div>' +
                '<div class="pop-up-row"><span class="pop-up-label">Habit: </span>' + habit + '</div>' +
                '<div class="pop-up-row"><span class="pop-up-label">Hardiness Zones: </span>' + hardinessDisplay + '</div>' +
                '<div class="pop-up-row"><span class="pop-up-label">Water Regime: </span>' + water_regime + '</div>' +
                '<div class="pop-up-row"><span class="pop-up-label">Exposure: </span>' + exposure + '</div>' +
                '<div class="pop-up-row"><span class="pop-up-label">Bloom Times: </span>' + bloomTimeDisplay + '</div>' +
                '<div class="pop-up-row"><span class="pop-up-label">Plant Size: </span>' + plant_size + '</div>' +
                '<div class="pop-up-row"><span class="pop-up-label">Garden Area: </span>' + garden_area + '</div>' +
                '<div class="pop-up-row"><span class="pop-up-label">Garden Name: </span>' + garden_name + '</div>' +
                '<div class="pop-up-row"><span class="pop-up-label">Garden Code: </span>' + garden_code + '</div>' +
                '<div class="pop-up-row"><span class="pop-up-label">Planted On: </span>' + planted_on + '</div>'
            )
            .addTo(map);
    });

    map.on('mouseenter', 'clusters', function () {
        map.getCanvas().style.cursor = 'pointer';
    });
    map.on('mouseleave', 'clusters', function () {
        map.getCanvas().style.cursor = '';
    });

    function filterByElementValue() {
        if (!map.getLayer('unclustered-point')) return;

        let value = normalize(filterEl.value);

        if (!value) {
            resetMapFilter(map);
            return;
        }

        let filtered = collections.filter(function (feature) {
            let cluster = feature.properties.cluster;
            let family = normalize(feature.properties.family_name || '');
            let genus = normalize(feature.properties.genus_name || '');
            return (!cluster && (family.indexOf(value) > -1 || genus.indexOf(value) > -1));
        });

        renderListings(filtered);

        if (filtered.length) {
            map.setFilter('unclustered-point', [
                'match',
                ['get', 'id'],
                filtered.map((feature) => feature.properties.id),
                true,
                false
            ]);
        }
    }

    filterEl.removeEventListener('keyup', filterByElementValue);
    filterEl.addEventListener('keyup', filterByElementValue);
}

const MAP_ICONS = {
    "Annual": "/static/plants/img/annual_icon.svg",
    "Bulb": "/static/plants/img/bulb_icon.svg",
    "Deciduous Shrub": "/static/plants/img/deciduous_shrub_icon.svg",
    "Deciduous Tree": "/static/plants/img/deciduous_tree_icon.svg",
    "Deciduous Vine": "/static/plants/img/vine_icon.svg",
    "Evergreen Groundcover": "/static/plants/img/evergreen_groundcover_icon.svg",
    "Evergreen Shrub": "/static/plants/img/evergreen_shrub_icon.svg",
    "Evergreen Tree": "/static/plants/img/evergreen_tree_icon.svg",
    "Evergreen Vine": "/static/plants/img/vine_icon.svg",
    "Grass": "/static/plants/img/grass_icon.svg",
    "Perennial": "/static/plants/img/perennial_icon.svg",
    "Succulent": "/static/plants/img/succulent_icon.svg",
};

// Rasterize an SVG to imageData and add to Mapbox under `name`
async function addSvgIcon(map, name, svgUrl, size = 64, pixelRatio = 2) {
    if (map.hasImage(name)) return;

    const res = await fetch(svgUrl, { cache: "force-cache" });
    if (!res.ok) throw new Error(`Failed to fetch SVG ${svgUrl}`);

    const svgText = await res.text();
    const blob = new Blob([svgText], { type: "image/svg+xml" });
    const objectUrl = URL.createObjectURL(blob);

    const img = new Image();
    img.decoding = "async";

    await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = reject;
        img.src = objectUrl;
    });

    const canvas = document.createElement("canvas");
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(img, 0, 0, size, size);

    URL.revokeObjectURL(objectUrl);

    const imageData = ctx.getImageData(0, 0, size, size);
    if (!map.hasImage(name)) {
        map.addImage(name, imageData, { pixelRatio });
    }
}

// Load all icons once
async function loadAllIcons(map) {
    const entries = Object.entries(MAP_ICONS);
    await Promise.all(
        entries.map(([name, url]) => addSvgIcon(map, name, url, 64, 2).catch((e) => {
            console.error("Icon load failed:", name, url, e);
        }))
    );
}

// ---------- Main setup ----------
async function initialMapSetup(map) {
    // 1) Images 
    await loadAllIcons(map);

    // 2) Fetch GeoJSON from endpoint (with page filters + bbox)
    const url = buildCollectionsGeojsonUrl(map);
    console.log("Fetching collections from:", url.toString());

    try {
        const response = await fetch(url.toString(), {
            headers: { "Accept": "application/json" },
        });

        if (!response.ok) {
            const text = await response.text().catch(() => "");
            throw new Error(`GeoJSON HTTP ${response.status}. Body starts: ${text.slice(0, 200)}`);
        }

        const featureCollection = await response.json();

        // 3) Source (guarded)
        ensureCollectionsSource(map, featureCollection);

        // 4) Layers (guarded)
        ensureLayer(map, {
            id: "clusters",
            type: "circle",
            source: "collections",
            filter: ["has", "point_count"],
            paint: {
                "circle-color": ["step", ["get", "point_count"], "#51bbd6", 100, "#f1f075", 750, "#f28cb1"],
                "circle-radius": ["step", ["get", "point_count"], 20, 100, 30, 750, 40],
            },
        });

        ensureLayer(map, {
            id: "cluster-count",
            type: "symbol",
            source: "collections",
            filter: ["has", "point_count"],
            layout: {
                "text-field": "{point_count_abbreviated}",
                "text-font": ["DIN Offc Pro Medium", "Arial Unicode MS Bold"],
                "text-size": 12,
            },
        });

        ensureLayer(map, {
            id: "unclustered-point",
            type: "symbol",
            source: "collections",
            filter: ["!", ["has", "point_count"]],
            layout: {
                "icon-image": ["get", "habit"],
                "icon-size": 2,
            },
        });

        hideLoader();
        renderListings([]);
    } catch (error) {
        console.error("Initial collections fetch failed:", error);
        hideLoader();
        if (listingEl) listingEl.innerHTML = "<p>Unable to load collections.</p>";
    }

    // 5) Bind interactions once (not duplicated on style change)
    bindHandlersOnce(map);

    bindMapFiltersForm(map);
}

// ---------------- Filters UI (no reload) ----------------
function buildQueryStringFromForm(formEl) {
    const params = new URLSearchParams();

    for (const el of formEl.elements) {
        if (!el.name) continue;
        if (el.disabled) continue;

        // Skip non-data controls
        if (el.type === "submit" || el.type === "button" || el.type === "reset") continue;
        if (el.name === "csrfmiddlewaretoken") continue;

        if (el.type === "checkbox") {
            if (el.checked) params.append(el.name, "1");
            continue;
        }

        if (el.tagName === "SELECT" && el.multiple) {
            for (const opt of el.selectedOptions) {
                const v = (opt.value || "").trim();
                if (v) params.append(el.name, v);
            }
            continue;
        }

        const v = (el.value || "").trim();
        if (!v) continue;
        params.append(el.name, v);
    }

    return params.toString();
}

function setActiveFiltersIndicator(qs) {
    const el = document.getElementById("active-filters");
    if (!el) return;

    if (!qs) {
        el.textContent = "No active filters";
        return;
    }

    // Human-friendly decode
    const pretty = decodeURIComponent(qs.replace(/\+/g, " "));
    el.textContent = `Active filters: ${pretty}`;
}

function bindMapFiltersForm(map) {
    const formEl = document.getElementById("map-filters-form");
    if (!formEl) return;

    // Initialize indicator from current URL
    setActiveFiltersIndicator(window.location.search.replace(/^\?/, ""));

    formEl.addEventListener("submit", async (e) => {
        e.preventDefault();

        const qs = buildQueryStringFromForm(formEl);

        // Update browser URL without reload
        const newUrl = `${window.location.pathname}${qs ? "?" + qs : ""}`;
        window.history.replaceState({}, "", newUrl);

        setActiveFiltersIndicator(qs);

        // Refresh GeoJSON source with new filters + current bbox
        await refreshCollectionsData(map);

        // Clear sidebar listing until moveend repopulates from rendered features
        if (listingEl) listingEl.innerHTML = "<p>Drag the map to populate results</p>";
        resetMapFilter(map);
    });

    const resetBtn = document.getElementById("filters-reset");
    if (resetBtn) {
        resetBtn.addEventListener("click", async () => {
            formEl.reset();

            // Clear URL
            window.history.replaceState({}, "", window.location.pathname);
            setActiveFiltersIndicator("");

            await refreshCollectionsData(map);

            if (listingEl) listingEl.innerHTML = "<p>Drag the map to populate results</p>";
            resetMapFilter(map);
        });
    }
}

map.on('load', function () {
    (async () => {
        await initialMapSetup(map);
    })();
});
