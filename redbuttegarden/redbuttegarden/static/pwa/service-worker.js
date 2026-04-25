const CACHE_VERSION = "v6"; // bump on deploy
const STATIC_CACHE = `static-${CACHE_VERSION}`;
const DATA_CACHE = `data-${CACHE_VERSION}`;
const PAGE_CACHE = `pages-${CACHE_VERSION}`;

// Keep this small. Do NOT pre-cache the whole site.
const PRECACHE_STATIC_URLS = [
  "/static/plants/css/plant_map.css",
  "/static/plants/js/plant_map.js",
  "/static/plants/js/name_styling.js",
  "/static/manifest.webmanifest",
  "/static/redbuttegarden/img/favicon/icon-192x192.png",
  "/static/redbuttegarden/img/favicon/icon-512x512.png",
];

const PRECACHE_PAGE_URLS = [
  "/plants/plant-map/",
  "/offline/",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    Promise.all([
      caches.open(STATIC_CACHE).then((cache) => cache.addAll(PRECACHE_STATIC_URLS)),
      caches.open(PAGE_CACHE).then((cache) => cache.addAll(PRECACHE_PAGE_URLS)),
    ])
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    const allow = new Set([STATIC_CACHE, DATA_CACHE, PAGE_CACHE]);
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
    url.pathname.includes("/preview/") ||
    url.searchParams.has("preview")
  ) {
    return; // let network handle it
  }

  // ---- HTML navigations (pages) ----
  if (req.mode === "navigate") {
    if (PRECACHE_PAGE_URLS.includes(url.pathname)) {
      event.respondWith(networkFirstPage(req));
      return;
    }
    event.respondWith(networkOnlyHtml(req));
    return;
  }

  // ---- Data endpoints ----
  if (url.pathname === "/plants/api/collections-geojson/") {
    event.respondWith(staleWhileRevalidate(req, DATA_CACHE));
    return;
  }

  // ---- Static assets ----
  if (url.pathname.startsWith("/static/")) {
    if (url.pathname.endsWith(".js") || url.pathname.endsWith(".css")) {
      event.respondWith(networkFirstStatic(req));
      return;
    }
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

async function networkFirstStatic(request) {
  const cache = await caches.open(STATIC_CACHE);
  try {
    const resp = await fetch(request, { cache: "no-store" });
    if (resp.ok) cache.put(request, resp.clone());
    return resp;
  } catch (e) {
    const cached = await cache.match(request);
    return cached || new Response("", { status: 504 });
  }
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

async function networkFirstPage(request) {
  const cache = await caches.open(PAGE_CACHE);
  try {
    const resp = await fetch(request, { cache: "no-store" });
    if (resp.ok) cache.put(request, resp.clone());
    return resp;
  } catch (e) {
    const cached = await cache.match(request);
    if (cached) return cached;
    return offlineFallback();
  }
}

async function networkOnlyHtml(request) {
  try {
    return await fetch(request, { cache: "no-store" });
  } catch (e) {
    return offlineFallback();
  }
}

async function offlineFallback() {
  const offline = await caches.open(PAGE_CACHE).then((c) => c.match("/offline/"));
  return offline || new Response("Offline", { status: 200, headers: { "Content-Type": "text/plain" } });
}
