const CACHE_NAME = "plant-map-v1";
const APP_SHELL = [
    "/plants/plant-map/",
    "/static/plants/css/plant_map.css",
    "/static/plants/js/plant_map.js",
    "/static/plants/js/name_styling.js",
    "/static/manifest.webmanifest",
    "/static/pwa/icon-192.png",
    "/static/pwa/icon-512.png",
];

self.addEventListener("install", (event) => {
    event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)));
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
        )
    );
    self.clients.claim();
});

self.addEventListener("fetch", (event) => {
    const url = new URL(event.request.url);

    if (url.origin !== self.location.origin) return;

    if (url.pathname === "/plants/api/collections-geojson/") {
        event.respondWith(staleWhileRevalidate(event.request));
        return;
    }

    event.respondWith(cacheFirst(event.request));
});

async function cacheFirst(request) {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(request);
    if (cached) return cached;

    const resp = await fetch(request);
    if (request.method === "GET" && resp.ok) cache.put(request, resp.clone());
    return resp;
}

async function staleWhileRevalidate(request) {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(request);

    const fetchPromise = fetch(request)
        .then((resp) => {
            if (resp.ok) cache.put(request, resp.clone());
            return resp;
        })
        .catch(() => null);

    return cached || (await fetchPromise) || new Response("{}", { headers: { "Content-Type": "application/json" } });
}