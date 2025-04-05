const mapboxToken = JSON.parse(document.getElementById('mapboxToken').textContent);

mapboxgl.accessToken = mapboxToken;
let map = new mapboxgl.Map({
    container: 'map', // container ID
    style: 'mapbox://styles/auslaner/ckrdvnurq2ix018o34dv8sxft', // style URL
    center: [-111.823807, 40.766367], // starting position [lng, lat]
    zoom: 16 // starting zoom
});

if (isMobile()) {
    const geolocateControl = new mapboxgl.GeolocateControl({
        positionOptions: {
            enableHighAccuracy: true
        },
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

        // Only change from default RBG custom style if something else is selected
        if (layerId !== 'rbg-custom') {
            map.setStyle('mapbox://styles/mapbox/' + layerId);
        }

        map.once('styledata', () => {
            initialMapSetup(map);
        })
    };
}

// Holds visible collection features for filtering
let collections = [];

// Create a popup, but don't add it to the map yet.
let popup = new mapboxgl.Popup({
    closeButton: false
});

let filterEl = document.getElementById('feature-filter');
let listingEl = document.getElementById('feature-listing');

function isMobile() {
    return /Mobi|Android|iPhone|iPad|iPod|BlackBerry|Windows Phone/i.test(navigator.userAgent);
}

function renderListings(features) {
    features.sort((a, b) =>
        (a.properties.family_name > b.properties.family_name) ? 1 :
            (a.properties.family_name === b.properties.family_name) ? ((a.properties.genus_name > b.properties.genus_name) ? 1 :
                (a.properties.genus_name === b.properties.genus_name) ? ((a.properties.species_name > b.properties.species_name) ? 1 : -1) : -1) : -1);
    let empty = document.createElement('p');
    // Clear any existing listings
    listingEl.innerHTML = '';
    if (features.length) {
        features.forEach(function (feature) {
            if (!feature.properties.cluster) {
                let prop = feature.properties;
                let collection = document.createElement('a');
                collection.href = "/plants/collection/" + prop.id + "/";
                collection.target = '_blank';
                collection.innerHTML =
                    '<div class="feature-listing">' + prop.family_name + ' ' +
                    style_full_name(prop.species_full_name) +
                    '</div>';
                collection.addEventListener('mouseover', function () {
                    // Highlight corresponding feature on the map
                    popup
                        .setLngLat(feature.geometry.coordinates)
                        .setHTML(style_full_name(prop.species_full_name))
                        .addTo(map);
                });
                listingEl.appendChild(collection);
            }
        });

        // Show the filter input
        filterEl.parentNode.style.display = 'block';
    } else if (features.length === 0 && filterEl.value !== '') {
        empty.textContent = 'No results found';
        listingEl.appendChild(empty);
    } else {
        empty.textContent = 'Drag the map to populate results';
        listingEl.appendChild(empty);

        // Hide the filter input
        filterEl.parentNode.style.display = 'none';

        // remove features filter
        map.setFilter('unclustered-point', ['has', 'id']);
    }
}

function normalize(string) {
    return string.trim().toLowerCase();
}

function getUniqueFeatures(array, comparatorProperty) {
    let existingFeatureKeys = {};
    // Because features come from tiled vector data, feature geometries may be split
    // or duplicated across tile boundaries and, as a result, features may appear
    // multiple times in query results.
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
    map.setFilter('unclustered-point', ['has', 'id']);
}

function initialMapSetup(map) {
    // Add a new source from our GeoJSON data and
    // set the 'cluster' option to true. GL-JS will
    // add the point_count property to your source data.

    // Load all the icon images
    map.loadImage('/static/plants/img/annual_icon.png', function (error, image) {
        if (error) throw error;

        map.addImage('Annual', image);
    });
    map.loadImage('/static/plants/img/bulb_icon.png', function (error, image) {
        if (error) throw error;

        map.addImage('Bulb', image);
    });
    map.loadImage('/static/plants/img/deciduous_shrub_icon.png', function (error, image) {
        if (error) throw error;

        map.addImage('Deciduous Shrub', image);
    });
    map.loadImage('/static/plants/img/deciduous_tree_icon.png', function (error, image) {
        if (error) throw error;

        map.addImage('Deciduous Tree', image);
    });
    map.loadImage('/static/plants/img/evergreen_groundcover_icon.png', function (error, image) {
        if (error) throw error;

        map.addImage('Evergreen Groundcover', image);
    });
    map.loadImage('/static/plants/img/evergreen_shrub_icon.png', function (error, image) {
        if (error) throw error;

        map.addImage('Evergreen Shrub', image);
    });
    map.loadImage('/static/plants/img/evergreen_tree_icon.png', function (error, image) {
        if (error) throw error;

        map.addImage('Evergreen Tree', image);
    });
    map.loadImage('/static/plants/img/vine_icon.png', function (error, image) {
        if (error) throw error;

        map.addImage('Deciduous Vine', image);
        map.addImage('Evergreen Vine', image);
    });
    map.loadImage('/static/plants/img/grass_icon.png', function (error, image) {
        if (error) throw error;

        map.addImage('Grass', image);
    });
    map.loadImage('/static/plants/img/perennial_icon.png', function (error, image) {
        if (error) throw error;

        map.addImage('Perennial', image);
    });
    map.loadImage('/static/plants/img/succulent_icon.png', function (error, image) {
        if (error) throw error;

        map.addImage('Succulent', image);
    });

    // If URL includes parameters send ajax request for filtered collections
    // Otherwise, load geojson file of all collections
    if (window.location.href.includes('?')) {
        $.ajax({
            url: '{{ request.get_full_path }}',
            success: function (data) {
                const filteredCollections = JSON.parse(data);

                map.addSource('collections', {
                    type: 'geojson',
                    data: filteredCollections,
                    cluster: true,
                    clusterMaxZoom: 17, // Max zoom to cluster points on
                    clusterRadius: 40 // Radius of each cluster when clustering points (defaults to 50)
                });

                map.addLayer({
                    id: 'clusters',
                    type: 'circle',
                    source: 'collections',
                    filter: ['has', 'point_count'],
                    paint: {
                        // Use step expressions (https://docs.mapbox.com/mapbox-gl-js/style-spec/#expressions-step)
                        // with three steps to implement three types of circles:
                        //   * Blue, 20px circles when point count is less than 100
                        //   * Yellow, 30px circles when point count is between 100 and 750
                        //   * Pink, 40px circles when point count is greater than or equal to 750
                        'circle-color': [
                            'step',
                            ['get', 'point_count'],
                            '#51bbd6',
                            100,
                            '#f1f075',
                            750,
                            '#f28cb1'
                        ],
                        'circle-radius': [
                            'step',
                            ['get', 'point_count'],
                            20,
                            100,
                            30,
                            750,
                            40
                        ]
                    }
                });

                map.addLayer({
                    id: 'cluster-count',
                    type: 'symbol',
                    source: 'collections',
                    filter: ['has', 'point_count'],
                    layout: {
                        'text-field': '{point_count_abbreviated}',
                        'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
                        'text-size': 12
                    }
                });

                map.addLayer({
                    id: 'unclustered-point',
                    type: 'symbol',
                    source: 'collections',
                    filter: ['!', ['has', 'point_count']],
                    layout: {
                        'icon-image': ['get', 'habit'],
                        'icon-size': 2
                    }
                });

                document.getElementById("map-load-overlay").style.display = "none";

                // Call this function on initialization
                // passing an empty array to render an empty state
                renderListings([]);
            }
        });

    } else {
        map.addSource('collections', {
            type: 'geojson',
            data: `https://${window.location.hostname}/media/collections.geojson`,
            cluster: true,
            clusterMaxZoom: 17, // Max zoom to cluster points on
            clusterRadius: 40 // Radius of each cluster when clustering points (defaults to 50)
        });

        map.addLayer({
            id: 'clusters',
            type: 'circle',
            source: 'collections',
            filter: ['has', 'point_count'],
            paint: {
                // Use step expressions (https://docs.mapbox.com/mapbox-gl-js/style-spec/#expressions-step)
                // with three steps to implement three types of circles:
                //   * Blue, 20px circles when point count is less than 100
                //   * Yellow, 30px circles when point count is between 100 and 750
                //   * Pink, 40px circles when point count is greater than or equal to 750
                'circle-color': [
                    'step',
                    ['get', 'point_count'],
                    '#51bbd6',
                    100,
                    '#f1f075',
                    750,
                    '#f28cb1'
                ],
                'circle-radius': [
                    'step',
                    ['get', 'point_count'],
                    20,
                    100,
                    30,
                    750,
                    40
                ]
            }
        });

        map.addLayer({
            id: 'cluster-count',
            type: 'symbol',
            source: 'collections',
            filter: ['has', 'point_count'],
            layout: {
                'text-field': '{point_count_abbreviated}',
                'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
                'text-size': 12
            }
        });

        map.addLayer({
            id: 'unclustered-point',
            type: 'symbol',
            source: 'collections',
            filter: ['!', ['has', 'point_count']],
            layout: {
                'icon-image': ['get', 'habit'],
                'icon-size': 2
            }
        });

        document.getElementById("map-load-overlay").style.display = "none";

        // Call this function on initialization
        // passing an empty array to render an empty state
        renderListings([]);
    }

    map.on('movestart', function () {
        // reset features filter as the map starts moving
        resetMapFilter(map);
    });

    map.on('moveend', function () {
        let features = map.queryRenderedFeatures({layers: ['clusters', 'unclustered-point']});

        if (features) {
            let uniqueFeatures = getUniqueFeatures(features, 'id');
            // Populate features for the listing overlay.
            renderListings(uniqueFeatures);

            // Store the current features in `collections` variable to
            // later use for filtering on `keyup`.
            collections = uniqueFeatures;
        }
    });

    // inspect a cluster on click
    map.on('click', 'clusters', function (e) {
        var features = map.queryRenderedFeatures(e.point, {
            layers: ['clusters']
        });
        var clusterId = features[0].properties.cluster_id;
        map.getSource('collections').getClusterExpansionZoom(
            clusterId,
            function (err, zoom) {
                if (err) return;

                map.easeTo({
                    center: features[0].geometry.coordinates,
                    zoom: zoom
                });
            }
        );
    });

    // When a click event occurs on a feature in
    // the unclustered-point layer, open a popup at
    // the location of the feature, with
    // description HTML from its properties.
    map.on('click', 'unclustered-point', function (e) {
        const coordinates = e.features[0].geometry.coordinates.slice();
        const family_name = e.features[0].properties.family_name;
        const genus_name = e.features[0].properties.genus_name;
        const species_name = e.features[0].properties.species_name;
        const species_full_name = e.features[0].properties.species_full_name;
        const species_id = e.features[0].properties.species_id;
        const collection_id = e.features[0].properties.id;
        const vernacular_name = e.features[0].properties.vernacular_name;
        const habit = e.features[0].properties.habit;
        const hardiness = e.features[0].properties.hardiness;
        const water_regime = e.features[0].properties.water_regime;
        const exposure = e.features[0].properties.exposure;
        const bloom_time = e.features[0].properties.bloom_time;
        const plant_size = e.features[0].properties.plant_size;
        const garden_area = e.features[0].properties.garden_area;
        const garden_name = e.features[0].properties.garden_name;
        const garden_code = e.features[0].properties.garden_code;
        const planted_on = e.features[0].properties.planted_on;

        const formatted_species_full_name = formatSpeciesFullName(species_id, species_full_name);

        // Ensure that if the map is zoomed out such that
        // multiple copies of the feature are visible, the
        // popup appears over the copy being pointed to.
        while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
            coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
        }

        new mapboxgl.Popup()
            .setLngLat(coordinates)
            .setHTML(
                '<div class="pop-up-row">' +
                '<a href="/plants/collection/' + collection_id + '/">Collection Detail Page</a>' +
                '</div>' +
                '<div class="pop-up-row">' +
                '<span class="pop-up-label">Family Name: </span>' + family_name +
                '</div>' +
                '<div class="pop-up-row">' +
                '<span class="pop-up-label">Genus Name: </span><span class="scientific-name">' + genus_name + '</span>' +
                '</div>' +
                '<div class="pop-up-row">' +
                '<span class="pop-up-label">Species Name: </span><span class="scientific-name">' + species_name + '</span>' +
                '</div>' +
                '<div class="pop-up-row">' +
                formatted_species_full_name +
                '</div>' +
                '<div class="pop-up-row">' +
                '<span class="pop-up-label">Vernacular Name: </span>' + vernacular_name +
                '</div>' +
                '<div class="pop-up-row">' +
                '<span class="pop-up-label">Habit: </span>' + habit +
                '</div>' +
                '<div class="pop-up-row">' +
                '<span class="pop-up-label">Hardiness: </span>' + hardiness +
                '</div>' +
                '<div class="pop-up-row">' +
                '<span class="pop-up-label">Water Regime: </span>' + water_regime +
                '</div>' +
                '<div class="pop-up-row">' +
                '<span class="pop-up-label">Exposure: </span>' + exposure +
                '</div>' +
                '<div class="pop-up-row">' +
                '<span class="pop-up-label">Bloom Times: </span>' + bloom_time +
                '</div>' +
                '<div class="pop-up-row">' +
                '<span class="pop-up-label">Plant Size: </span>' + plant_size +
                '</div>' +
                '<div class="pop-up-row">' +
                '<span class="pop-up-label">Garden Area: </span>' + garden_area +
                '</div>' +
                '<div class="pop-up-row">' +
                '<span class="pop-up-label">Garden Name: </span>' + garden_name +
                '</div>' +
                '<div class="pop-up-row">' +
                '<span class="pop-up-label">Garden Code: </span>' + garden_code +
                '</div>' +
                '<div class="pop-up-row">' +
                '<span class="pop-up-label">Planted On: </span>' + planted_on +
                '</div>'
            )
            .addTo(map);

        console.log(e.features[0]);
    });

    map.on('mouseenter', 'clusters', function () {
        map.getCanvas().style.cursor = 'pointer';
    });
    map.on('mouseleave', 'clusters', function () {
        map.getCanvas().style.cursor = '';
    });

    function formatSpeciesFullName(species_id, species_full_name) {
        if (species_id) {
            return '<span class="pop-up-label">Full Name: </span><a href="/plants/species/' + species_id + '/"' +
                style_full_name(species_full_name) + '</a>'
        } else {
            return '<span class="pop-up-label">Full Name: </span>' +
                style_full_name(species_full_name)
        }
    }

    function filterByElementValue() {
        let value = normalize(filterEl.value);

        if (!value) {
            resetMapFilter(map);
            return
        }

        // Filter visible features that don't match the input value.
        let filtered = collections.filter(function (feature) {
            let cluster = feature.properties.cluster;
            let family = normalize(feature.properties.family_name || '');
            let genus = normalize(feature.properties.genus_name || '');
            return !cluster && family.indexOf(value) > -1 || genus.indexOf(value) > -1;
        });

        // Populate the sidebar with filtered results
        renderListings(filtered);

        // Set the filter to populate features into the layer.
        if (filtered.length) {
            map.setFilter('unclustered-point', [
                'match',
                ['get', 'id'],
                filtered.map(function (feature) {
                    return feature.properties.id;
                }),
                true,
                false
            ]);
        }
    }

    filterEl.addEventListener('keyup', filterByElementValue);
}

map.on('load', function () {
    initialMapSetup(map);
});
