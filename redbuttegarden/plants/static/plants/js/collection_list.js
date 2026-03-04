/* global htmx */
(() => {
    function addFormControl() {
        const container = document.getElementById("collection-filter-form");
        if (!container) return;

        const controls = container.querySelectorAll(
            'input[type="text"], input[type="search"], select, textarea'
        );
        controls.forEach((el) => {
            if (!el.classList.contains("form-control")) el.classList.add("form-control");
        });

        const bools = container.querySelectorAll(
            'input[type="checkbox"], input[type="radio"]'
        );
        bools.forEach((el) => {
            if (!el.classList.contains("form-check-input")) {
                el.classList.add("form-check-input");
            }
        });
    }

    function setupCleanGetSubmit() {
        const form = document.getElementById("collection-filter-form");
        if (!form) return;

        form.addEventListener("submit", () => {
            const els = form.querySelectorAll("input, select, textarea");

            els.forEach((el) => {
                if (!el.name) return;

                // Keep HTMX marker and any other hidden fields
                if (el.type === "hidden") return;

                if (el.type === "checkbox" || el.type === "radio") {
                    if (!el.checked) el.disabled = true;
                    return;
                }

                if ((el.value || "").trim() === "") {
                    el.disabled = true;
                }
            });

            // Re-enable immediately after submission so the form isn't left disabled
            window.setTimeout(() => {
                els.forEach((el) => {
                    el.disabled = false;
                });
            }, 0);
        });
    }

    function setupHtmxPaginationIntercept() {
        let pendingPush = null;

        document.body.addEventListener("click", (e) => {
            const a = e.target.closest("#table-container a");
            if (!a) return;

            const href = a.getAttribute("href") || "";
            if (!href) return;

            if (a.dataset && a.dataset.noHtmx === "true") return;

            if (
                href.includes("_export=") ||
                a.target === "_blank" ||
                a.hasAttribute("download")
            ) {
                return;
            }

            const isPagination = !!a.closest(".pagination");
            const hasPageParam = /[?&]page=\d+/.test(href);
            const explicitOptIn = a.classList.contains("js-htmx-link");

            if (!isPagination && !hasPageParam && !explicitOptIn) return;

            e.preventDefault();

            if (typeof window.htmx === "undefined") {
                window.location.href = href;
                return;
            }

            pendingPush = href;

            htmx.ajax("GET", href, {
                target: "#table-container",
                swap: "outerHTML",
                pushUrl: true,
            });
        });

        document.body.addEventListener("htmx:afterSwap", () => {
            addFormControl();
            setupCleanGetSubmit(); // form may have been swapped/replaced

            if (!pendingPush) return;
            try {
                history.pushState({}, "", pendingPush);
            } finally {
                pendingPush = null;
            }
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        addFormControl();
        setupCleanGetSubmit();
        setupHtmxPaginationIntercept();
    });

    document.body.addEventListener("htmx:afterSwap", () => {
        addFormControl();
        setupCleanGetSubmit();
    });
})();

(() => {
    function pruneEmptyParams(evt) {
        // Only apply to our filter form
        const form = evt.target;
        if (!form || form.id !== "collection-filter-form") return;

        const params = evt.detail.parameters;

        // Remove empty string params: plant_id=&...
        Object.keys(params).forEach((key) => {
            if (params[key] === "" || params[key] == null) {
                delete params[key];
            }
        });

        // If you want to keep _hx=1, do nothing; if you want to drop it from URL pushes, delete it:
        // delete params._hx;
    }

    // HTMX hook: runs right before request is sent
    document.body.addEventListener("htmx:configRequest", pruneEmptyParams);
})();