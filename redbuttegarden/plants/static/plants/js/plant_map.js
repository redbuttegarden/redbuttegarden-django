window.initializeMapboxMap = function initializePlantMap() {
let refreshTimer = null;
const tokenElement = document.getElementById('mapboxToken');
const mapContainer = document.getElementById('map');

if (!tokenElement || !mapContainer) {
    throw new Error("Map details are unavailable.");
}

const mapboxToken = JSON.parse(tokenElement.textContent);

if (!mapboxToken) {
    throw new Error("Map token is unavailable.");
}

mapboxgl.accessToken = mapboxToken;
const map = new mapboxgl.Map({
    container: mapContainer,
    style: 'mapbox://styles/auslaner/ckrdvnurq2ix018o34dv8sxft',
    center: [-111.823807, 40.766367],
    zoom: 16
});

function syncViewListLink() {
    const link = document.getElementById("view-list-link");
    if (!link) return;

    const url = new URL(link.getAttribute("href"), window.location.origin);
    url.search = window.location.search;   // current filters
    url.searchParams.delete("bbox");        // optional: list page doesn't need bbox
    link.setAttribute("href", url.toString());
}

function buildQueryStringFromFormForLinks(formEl) {
    const params = new URLSearchParams();

    for (const el of formEl.elements) {
        if (!el.name) continue;
        if (el.disabled) continue;

        // Skip non-data controls
        if (el.type === "submit" || el.type === "button" || el.type === "reset") continue;

        if (el.type === "checkbox") {
            if (el.checked) params.append(el.name, "true");
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

let viewListBound = false;

function bindViewListLink() {
    if (viewListBound) return;
    viewListBound = true;

    const link = document.getElementById("view-list-link");
    const formEl = document.getElementById("map-filters-form");
    if (!link || !formEl) return;

    const baseHref = link.getAttribute("href");

    link.addEventListener("click", (e) => {
        e.preventDefault();

        // Build from current form state (works even if user never hit Apply)
        const qs = buildQueryStringFromFormForLinks(formEl);

        const dest = new URL(baseHref, window.location.origin);
        if (qs) dest.search = "?" + qs;

        window.location.assign(dest.toString());
    });
}

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
const layerList = document.getElementById("mapMenu");
const inputs = layerList ? layerList.getElementsByTagName("input") : [];

for (const input of inputs) {
    input.onclick = (layer) => {
        const layerId = layer.target.id;

        if (layerId !== 'rbg-custom') {
            map.setStyle('mapbox://styles/mapbox/' + layerId);
        }

        map.once('style.load', () => {
            bindViewListLink();
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
    listingEl.replaceChildren();

    if (features.length) {
        features.forEach(function (feature) {
            if (!feature.properties.cluster) {
                let prop = feature.properties;
                let collection = document.createElement('a');
                collection.href = "/plants/collection/" + prop.id + "/";
                collection.target = '_blank';
                collection.rel = 'noopener';
                const name = document.createElement('div');
                name.className = 'feature-listing';
                name.textContent = `${prop.family_name || ''} ${prop.species_full_name || ''}`.trim();
                collection.append(name);
                collection.addEventListener('mouseover', function () {
                    popup
                        .setLngLat(feature.geometry.coordinates)
                        .setText(prop.species_full_name || '')
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

    // Copy current query params, excluding UI-only params
    const current = new URLSearchParams(window.location.search);
    const dropKeys = new Set(["page", "_export", "_hx", "mode"]);

    for (const [k, v] of current.entries()) {
        if (dropKeys.has(k)) continue;
        // Keep multiple values if present (URLSearchParams.entries already iterates them)
        url.searchParams.append(k, v);
    }

    // Add bbox if map bounds are available
    try {
        const b = map.getBounds();
        url.searchParams.set(
            "bbox",
            [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()].join(",")
        );
    } catch (e) { }

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

function createPopupRow(label, value) {
    const row = document.createElement('div');
    row.className = 'pop-up-row';
    const labelElement = document.createElement('span');
    labelElement.className = 'pop-up-label';
    labelElement.textContent = `${label}: `;
    row.append(labelElement, document.createTextNode(value || 'Not recorded'));
    return row;
}

function displayList(value) {
    if (!value) return "";
    try {
        const values = Array.isArray(value) ? value : JSON.parse(value);
        if (Array.isArray(values)) return values.join(", ");
    } catch {
        if (typeof value === "string") {
            return value.split(",").map((item) => item.trim()).filter(Boolean).join(", ");
        }
    }
    return "";
}

function createCollectionPopupContent(properties) {
    const container = document.createElement('div');
    const detailRow = document.createElement('div');
    detailRow.className = 'pop-up-row';
    const detailLink = document.createElement('a');
    detailLink.href = `/plants/collection/${properties.id}/`;
    detailLink.textContent = 'Collection detail page';
    detailRow.append(detailLink);
    container.append(detailRow);
    [
        ['Family Name', properties.family_name], ['Genus Name', properties.genus_name],
        ['Species Name', properties.species_name], ['Full Name', properties.species_full_name],
        ['Vernacular Name', properties.vernacular_name], ['Habit', properties.habit],
        ['Hardiness Zones', displayList(properties.hardiness)], ['Water Regime', properties.water_regime],
        ['Exposure', properties.exposure], ['Bloom Times', displayList(properties.bloom_time)],
        ['Plant Size', properties.plant_size], ['Garden Area', properties.garden_area],
        ['Garden Name', properties.garden_name], ['Garden Code', properties.garden_code],
        ['Planted On', properties.planted_on],
    ].forEach(([label, value]) => container.append(createPopupRow(label, value)));
    return container;
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

    map.on("moveend", function () {
        // Debounced refresh for bbox
        clearTimeout(refreshTimer);
        refreshTimer = setTimeout(async () => {
            await refreshCollectionsData(map);

            map.once("idle", () => {
                const layers = [];
                if (map.getLayer("clusters")) layers.push("clusters");
                if (map.getLayer("unclustered-point")) layers.push("unclustered-point");
                if (!layers.length) return;

                const features = map.queryRenderedFeatures({ layers });
                const uniqueFeatures = getUniqueFeatures(features || [], "id");
                renderListings(uniqueFeatures);
                collections = uniqueFeatures;
            });
        }, 350);
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

        while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
            coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
        }

        new mapboxgl.Popup()
            .setLngLat(coordinates)
            .setDOMContent(createCollectionPopupContent(f.properties))
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
        if (listingEl) listingEl.textContent = "Unable to load collections.";
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
            if (el.checked) params.append(el.name, "true");
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

    syncViewListLink();

    formEl.addEventListener("submit", async (e) => {
        e.preventDefault();

        const qs = buildQueryStringFromForm(formEl);

        // Update browser URL without reload
        const newUrl = `${window.location.pathname}${qs ? "?" + qs : ""}`;
        window.history.replaceState({}, "", newUrl);

        setActiveFiltersIndicator(qs);
        syncViewListLink();

        await refreshCollectionsData(map);
        map.once("idle", () => {
            const layers = [];
            if (map.getLayer("clusters")) layers.push("clusters");
            if (map.getLayer("unclustered-point")) layers.push("unclustered-point");
            if (!layers.length) return;
            const features = map.queryRenderedFeatures({ layers });
            const uniqueFeatures = getUniqueFeatures(features || [], "id");
            renderListings(uniqueFeatures);
            collections = uniqueFeatures;
        });
        resetMapFilter(map);
    });

    const resetBtn = document.getElementById("filters-reset");
    if (resetBtn) {
        resetBtn.addEventListener("click", async () => {
            // Reset native controls (good for text inputs)
            formEl.reset();

            // Force-clear selects + checkboxes to "no filter"
            for (const el of formEl.elements) {
                if (!el.name) continue;
                if (el.disabled) continue;

                if (el.type === "checkbox") {
                    el.checked = false;
                    continue;
                }

                if (el.tagName === "SELECT") {
                    // Select the blank/placeholder option if it exists, else fall back to first option
                    const hasBlank = Array.from(el.options).some((opt) => opt.value === "");
                    el.value = hasBlank ? "" : (el.options[0]?.value ?? "");
                    continue;
                }

                if (el.type === "text" || el.type === "search" || el.tagName === "TEXTAREA") {
                    el.value = "";
                }
            }

            // Clear URL (what you already do)
            window.history.replaceState({}, "", window.location.pathname);
            setActiveFiltersIndicator("");

            // Keep View List correct (if you're building it from form, optional)
            // syncViewListLink();  // if you still use it; otherwise no-op

            await refreshCollectionsData(map);

            if (listingEl) listingEl.textContent = "Drag the map to populate results";
            resetMapFilter(map);
        });
    }
}

(() => {
    const details = document.getElementById("mapFilters");
    if (!details) return;

    const mqMobile = window.matchMedia("(max-width: 590px)");

    const syncDetails = () => {
        if (mqMobile.matches) {
            details.removeAttribute("open"); // collapsed on mobile
        } else {
            details.setAttribute("open", ""); // open on desktop
        }
    };

    // Run once on load
    syncDetails();

    // Keep it in sync if the viewport crosses the breakpoint
    if (typeof mqMobile.addEventListener === "function") {
        mqMobile.addEventListener("change", syncDetails);
    } else if (typeof mqMobile.addListener === "function") {
        // Safari fallback
        mqMobile.addListener(syncDetails);
    }
})();

map.on('load', function () {
    (async () => {
        await initialMapSetup(map);
    })();
});

return map;
};
