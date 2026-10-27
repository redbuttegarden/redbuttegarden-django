/**
 * Load Mapbox only after a visitor has shown intent to use the page.
 *
 * Public map pages are deliberately cacheable, so this client-side gate avoids
 * user-agent variants while preventing passive crawlers from requesting Mapbox.
 */
(() => {
    const MAPBOX_CSS_URL = "https://api.mapbox.com/mapbox-gl-js/v3.12.0/mapbox-gl.css";
    const MAPBOX_JS_URL = "https://api.mapbox.com/mapbox-gl-js/v3.12.0/mapbox-gl.js";
    const MAPBOX_CSS_INTEGRITY = "sha384-Sdx78Z6nqVgiCnAlgCe5s/P74CeyLMH/hI61WTXUO7kbN/HJ81e3MAkMTz1jxsm+";
    const MAPBOX_JS_INTEGRITY = "sha384-/TrjtPGu/gYA2W0pthEIcd2shlv/VWamCvc9tZ776cfv6X9dyG34BWLygYZeItjZ";
    let started = false;

    function setStatus(message) {
        document.querySelectorAll("[data-mapbox-status]").forEach((status) => {
            status.textContent = message;
        });
    }

    function setLoading(isLoading) {
        document.querySelectorAll("[data-mapbox-loading-overlay]").forEach((overlay) => {
            overlay.hidden = !isLoading;
        });
    }

    function setMapBusy(isBusy) {
        document.querySelectorAll("[data-mapbox-container]").forEach((container) => {
            container.setAttribute("aria-busy", String(isBusy));
        });
    }

    function setPlaceholder(hidden, message) {
        document.querySelectorAll("[data-mapbox-placeholder]").forEach((placeholder) => {
            placeholder.hidden = hidden;
        });
        document.querySelectorAll("[data-mapbox-placeholder-message]").forEach((element) => {
            element.textContent = message;
        });
    }

    function loadStylesheet() {
        return new Promise((resolve, reject) => {
            const stylesheet = document.createElement("link");
            stylesheet.rel = "stylesheet";
            stylesheet.href = MAPBOX_CSS_URL;
            stylesheet.integrity = MAPBOX_CSS_INTEGRITY;
            stylesheet.crossOrigin = "anonymous";
            stylesheet.onload = resolve;
            stylesheet.onerror = () => reject(new Error("Map stylesheet failed to load."));
            document.head.append(stylesheet);
        });
    }

    function loadScript() {
        return new Promise((resolve, reject) => {
            const script = document.createElement("script");
            script.src = MAPBOX_JS_URL;
            script.integrity = MAPBOX_JS_INTEGRITY;
            script.crossOrigin = "anonymous";
            script.onload = resolve;
            script.onerror = () => reject(new Error("Map script failed to load."));
            document.head.append(script);
        });
    }

    function waitForMap(map) {
        if (!map || typeof map.once !== "function") {
            return Promise.reject(new Error("Map initialization failed."));
        }

        if (typeof map.loaded === "function" && map.loaded()) {
            return Promise.resolve();
        }

        return new Promise((resolve, reject) => {
            map.once("load", resolve);
            map.once("error", () => reject(new Error("Map failed to load.")));
        });
    }

    async function startMap() {
        if (started) return;
        started = true;
        removeListeners();
        setLoading(true);
        setMapBusy(true);
        setPlaceholder(false, "Loading interactive map.");
        setStatus("Loading map.");

        try {
            await Promise.all([loadStylesheet(), loadScript()]);
            if (typeof window.initializeMapboxMap !== "function") {
                throw new Error("Map initializer is unavailable.");
            }
            const map = await window.initializeMapboxMap();
            await waitForMap(map);
            setLoading(false);
            setMapBusy(false);
            setPlaceholder(true, "");
            setStatus("Map loaded.");
        } catch {
            setLoading(false);
            setMapBusy(false);
            setPlaceholder(
                false,
                "The interactive map is currently unavailable. Location details remain available on this page."
            );
            setStatus("The map is currently unavailable.");
        }
    }

    function removeListeners() {
        document.removeEventListener("pointerdown", startMap);
        document.removeEventListener("touchstart", startMap);
        document.removeEventListener("keydown", startMap);
    }

    document.addEventListener("pointerdown", startMap, { passive: true });
    document.addEventListener("touchstart", startMap, { passive: true });
    document.addEventListener("keydown", startMap);
})();
