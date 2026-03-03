const CACHE_VERSION = "v2"; // bump on deploy
const STATIC_CACHE = `static-${CACHE_VERSION}`;
const DATA_CACHE = `data-${CACHE_VERSION}`;
const HTML_CACHE = `html-${CACHE_VERSION}`;

// Keep this small. Do NOT pre-cache the whole site.
const PRECACHE_URLS = [
  "/plants/plant-map/",
  "/static/plants/css/plant_map.css",
  "/static/plants/js/plant_map.js",
  "/static/plants/js/name_styling.js",
  "/static/manifest.webmanifest",
  "/static/redbuttegarden/img/favicon/icon-192x192.png",
  "/static/redbuttegarden/img/favicon/icon-512x512.png",
  "/offline/", // create a tiny offline page route
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => cache.addAll(PRECACHE_URLS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    const allow = new Set([STATIC_CACHE, DATA_CACHE, HTML_CACHE]);
    await Promise.all(keys.filter((k) => !allow.has(k)).map((k) => caches.delete(k)));
    await self.clients.claim();
  })());
});

// Allow the page to trigger immediate activation (nice for update UX)
self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});

self.addEventListener("fetch", (event) => {
  const req = event.request;

  // Only handle same-origin GET requests
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // ---- Never cache/admin/auth/preview areas ----
  if (
    url.pathname.startsWith("/admin/") ||
    url.pathname.startsWith("/nav-fragment/") ||
    url.pathname.startsWith("/django-admin/") ||
    url.pathname.startsWith("/api/token/") ||
    url.searchParams.has("preview")
  ) {
    return; // let network handle it
  }

  // ---- HTML navigations (pages) ----
  if (req.mode === "navigate") {
    event.respondWith(networkFirstHtml(req));
    return;
  }

  // ---- Data endpoints ----
  if (url.pathname === "/plants/api/collections-geojson/") {
    event.respondWith(staleWhileRevalidate(req, DATA_CACHE));
    return;
  }

  // ---- Static assets ----
  if (url.pathname.startsWith("/static/")) {
    event.respondWith(cacheFirst(req, STATIC_CACHE));
    return;
  }

  // ---- Media assets ----
  if (url.pathname.startsWith("/media/")) {
    return;  // don't handle; let browser/CDN handle it
  }

  // ---- Default: network-first for everything else ----
  event.respondWith(networkFirst(req));
});

async function cacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  if (cached) return cached;

  const resp = await fetch(request);
  if (resp.ok) cache.put(request, resp.clone());
  return resp;
}

async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);

  const fetchPromise = fetch(request)
    .then((resp) => {
      if (resp.ok) cache.put(request, resp.clone());
      return resp;
    })
    .catch(() => null);

  return cached || (await fetchPromise) || new Response("", { status: 504 });
}

async function networkFirst(request) {
  const cache = await caches.open(DATA_CACHE);
  try {
    const resp = await fetch(request);
    if (resp.ok) cache.put(request, resp.clone());
    return resp;
  } catch (e) {
    const cached = await cache.match(request);
    return cached || new Response("", { status: 504 });
  }
}

async function networkFirstHtml(request) {
  const cache = await caches.open(HTML_CACHE);

  try {
    // Use no-store to avoid weird interactions with browser HTTP cache
    const resp = await fetch(request, { cache: "no-store" });
    if (resp.ok) cache.put(request, resp.clone());
    return resp;
  } catch (e) {
    const cached = await cache.match(request);
    if (cached) return cached;

    // Offline fallback
    const offline = await caches.open(STATIC_CACHE).then((c) => c.match("/offline/"));
    return offline || new Response("Offline", { status: 200, headers: { "Content-Type": "text/plain" } });
  }
}