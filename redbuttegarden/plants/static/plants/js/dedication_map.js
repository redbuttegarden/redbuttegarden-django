/** Enhance the dedication map without mixing it into the plant-map dataset. */
window.initializeMapboxMap = function initializeDedicationMap() {
    const tokenElement = document.getElementById("mapboxToken");
    const listingElement = document.getElementById("feature-listing");
    const filterElement = document.getElementById("feature-filter");
    const token = tokenElement ? JSON.parse(tokenElement.textContent) : null;
    const mapContainer = document.getElementById("map");
    let map;
    let popup;
    let visibleFeatures = [];

    function text(value) { return value || "Not recorded"; }

    function setLoading(isLoading) {
        const overlay = document.getElementById("map-load-overlay");
        if (overlay) overlay.hidden = !isLoading;
    }

    function createRow(label, value) {
        const row = document.createElement("div");
        row.className = "pop-up-row";
        const labelElement = document.createElement("span");
        labelElement.className = "pop-up-label";
        labelElement.textContent = `${label}: `;
        row.append(labelElement, document.createTextNode(text(value)));
        return row;
    }

    function createPopupContent(properties) {
        const container = document.createElement("div");
        const linkRow = document.createElement("div");
        linkRow.className = "pop-up-row";
        const link = document.createElement("a");
        link.href = properties.detail_url || "#";
        link.textContent = "Dedication detail page";
        linkRow.append(link);
        container.append(linkRow, createRow("Honoree", properties.honoree), createRow("Garden", properties.garden_name), createRow("Garden area", properties.garden_area), createRow("Dedication ID", properties.dedication_id));
        return container;
    }

    function renderListings(features) {
        if (!listingElement || !filterElement) return;
        listingElement.replaceChildren();
        const unclustered = features.filter((feature) => !feature.properties.cluster);
        if (!unclustered.length) {
            const message = document.createElement("p");
            message.textContent = filterElement.value ? "No results found" : "Drag the map to populate results";
            listingElement.append(message);
            filterElement.parentElement.style.display = "none";
            return;
        }
        unclustered.sort((first, second) => text(first.properties.honoree).localeCompare(text(second.properties.honoree))).forEach((feature) => {
            const link = document.createElement("a");
            const properties = feature.properties;
            link.href = properties.detail_url || "#";
            link.target = "_blank";
            link.rel = "noopener";
            link.textContent = `${text(properties.honoree)} — ${text(properties.garden_name)}`;
            link.addEventListener("mouseover", () => {
                popup
                    .setLngLat(feature.geometry.coordinates)
                    .setDOMContent(createPopupContent(properties))
                    .addTo(map);
            });
            listingElement.append(link);
        });
        filterElement.parentElement.style.display = "block";
    }

    function getUniqueFeatures(features) {
        const identifiers = new Set();
        return features.filter((feature) => {
            const identifier = feature.properties.id;
            if (identifiers.has(identifier)) return false;
            identifiers.add(identifier);
            return true;
        });
    }

    async function loadDedications() {
        const endpoint = new URL("/plants/api/dedications-geojson/", window.location.origin);
        endpoint.search = window.location.search;
        const response = await fetch(endpoint, { headers: { Accept: "application/json" } });
        if (!response.ok) throw new Error(`GeoJSON HTTP ${response.status}`);
        const data = await response.json();
        const source = map.getSource("dedications");
        if (source) source.setData(data);
        else map.addSource("dedications", { type: "geojson", data, cluster: true, clusterMaxZoom: 17, clusterRadius: 40 });
    }

    function updateVisibleFeatures() {
        const layers = ["dedication-clusters", "dedication-points"].filter((layer) => map.getLayer(layer));
        if (!layers.length) return;
        visibleFeatures = getUniqueFeatures(map.queryRenderedFeatures({ layers }));
        renderListings(visibleFeatures);
    }

    function resetQuickFilter() {
        if (map.getLayer("dedication-points")) map.setFilter("dedication-points", ["!", ["has", "point_count"]]);
    }

    function filterVisibleDedications() {
        if (!filterElement || !map.getLayer("dedication-points")) return;
        const query = filterElement.value.trim().toLocaleLowerCase();
        if (!query) { resetQuickFilter(); renderListings(visibleFeatures); return; }
        const filtered = visibleFeatures.filter((feature) => !feature.properties.cluster && [feature.properties.honoree, feature.properties.garden_name, feature.properties.dedication_id].some((value) => String(value || "").toLocaleLowerCase().includes(query)));
        renderListings(filtered);
        map.setFilter("dedication-points", ["match", ["get", "id"], filtered.map((feature) => feature.properties.id), true, false]);
    }

    function setActiveFilters() {
        const indicator = document.getElementById("active-filters");
        if (!indicator) return;
        const query = window.location.search.slice(1);
        indicator.textContent = query ? `Active filters: ${decodeURIComponent(query.replace(/\+/g, " "))}` : "No active filters";
    }

    function bindForm() {
        const form = document.getElementById("map-filters-form");
        if (!form) return;
        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            const query = new URLSearchParams(new FormData(form));
            for (const [key, value] of [...query]) if (!value.trim()) query.delete(key);
            window.history.replaceState({}, "", `${window.location.pathname}${query.size ? `?${query}` : ""}`);
            setActiveFilters();
            await loadDedications();
            resetQuickFilter();
            map.once("idle", updateVisibleFeatures);
        });
        document.getElementById("filters-reset")?.addEventListener("click", async () => {
            form.reset();
            window.history.replaceState({}, "", window.location.pathname);
            setActiveFilters();
            await loadDedications();
            resetQuickFilter();
            map.once("idle", updateVisibleFeatures);
        });
    }

    function addLayers() {
        if (map.getLayer("dedication-clusters")) return;
        map.addLayer({ id: "dedication-clusters", type: "circle", source: "dedications", filter: ["has", "point_count"], paint: { "circle-color": ["step", ["get", "point_count"], "#51bbd6", 100, "#f1f075", 750, "#f28cb1"], "circle-radius": ["step", ["get", "point_count"], 20, 100, 30, 750, 40] } });
        map.addLayer({ id: "dedication-cluster-count", type: "symbol", source: "dedications", filter: ["has", "point_count"], layout: { "text-field": "{point_count_abbreviated}", "text-font": ["DIN Offc Pro Medium", "Arial Unicode MS Bold"], "text-size": 12 } });
        map.addLayer({ id: "dedication-points", type: "circle", source: "dedications", filter: ["!", ["has", "point_count"]], paint: { "circle-color": "#404", "circle-radius": 8, "circle-stroke-width": 2, "circle-stroke-color": "#fff" } });
    }

    if (!token || !mapContainer || !window.mapboxgl) {
        throw new Error("Map token is unavailable.");
    }
    mapboxgl.accessToken = token;
    popup = new mapboxgl.Popup({ closeButton: false });
    map = new mapboxgl.Map({ container: mapContainer, style: "mapbox://styles/auslaner/ckrdvnurq2ix018o34dv8sxft", center: [-111.823807, 40.766367], zoom: 16 });
    map.on("load", async () => {
        try {
            await loadDedications(); addLayers(); setLoading(false); renderListings([]); bindForm(); setActiveFilters();
            if (filterElement) filterElement.addEventListener("input", filterVisibleDedications);
        } catch (error) {
            setLoading(false);
            if (listingElement) listingElement.textContent = "Unable to load dedications.";
        }
    });
    document.querySelectorAll("#mapMenu input").forEach((input) => input.addEventListener("click", () => { if (input.id !== "rbg-custom") map.setStyle(`mapbox://styles/mapbox/${input.id}`); }));
    map.on("style.load", async () => { await loadDedications(); addLayers(); });
    map.on("moveend", () => map.once("idle", updateVisibleFeatures));
    map.on("click", "dedication-clusters", (event) => {
        const feature = map.queryRenderedFeatures(event.point, { layers: ["dedication-clusters"] })[0];
        map.getSource("dedications").getClusterExpansionZoom(feature.properties.cluster_id, (error, zoom) => { if (!error) map.easeTo({ center: feature.geometry.coordinates, zoom }); });
    });
    map.on("click", "dedication-points", (event) => {
        const feature = event.features[0];
        new mapboxgl.Popup().setLngLat(feature.geometry.coordinates).setDOMContent(createPopupContent(feature.properties)).addTo(map);
    });
    return map;
};
