function hardResetFilterForm(form) {
    const els = form.querySelectorAll("input, select, textarea");

    els.forEach((el) => {
        if (!el.name) return;
        if (el.type === "hidden") return; // keep _hx and any other hidden markers

        if (el.type === "checkbox" || el.type === "radio") {
            el.checked = false;
            return;
        }

        if (el.tagName === "SELECT") {
            // Prefer blank option if present
            const hasBlank = Array.from(el.options).some((o) => o.value === "");
            el.value = hasBlank ? "" : (el.options[0]?.value ?? "");
            return;
        }

        // text/search/textarea/etc.
        el.value = "";
    });
}

function setupClearIntercept() {
    const form = document.getElementById("collection-filter-form");
    const clear = document.getElementById("collection-clear");
    if (!form || !clear) return;

    clear.addEventListener("click", (e) => {
        e.preventDefault();

        // 1) Reset UI values (defeats bfcache/autofill)
        hardResetFilterForm(form);

        // 2) Clean destination URL (should be something like /plants/collections/results/?mode=list)
        const baseUrl = new URL(
            clear.getAttribute("href") || window.location.pathname,
            window.location.origin
        );

        // Ensure we don't keep HTMX marker in pushed URLs
        baseUrl.searchParams.delete("_hx");

        const url = baseUrl.pathname + (baseUrl.search ? baseUrl.search : "");

        // 3) Temporarily disable all non-hidden fields so HTMX can't serialize stale values
        const els = form.querySelectorAll("input, select, textarea");
        const disabled = [];
        els.forEach((el) => {
            if (el.type === "hidden") return;
            if (el.disabled) return;
            el.disabled = true;
            disabled.push(el);
        });

        // 4) HTMX request to the clean URL (no form params)
        if (typeof window.htmx !== "undefined") {
            htmx.ajax("GET", url, {
                target: "#table-container",
                swap: "outerHTML",
                pushUrl: true,
            });
        } else {
            window.location.assign(url);
        }

        // 5) Re-enable fields immediately after request is queued
        window.setTimeout(() => {
            disabled.forEach((el) => (el.disabled = false));
        }, 0);
    });
}

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
            setupClearIntercept(); // clear button/form may have been swapped/replaced

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
        setupClearIntercept();
    });

    document.body.addEventListener("htmx:afterSwap", () => {
        addFormControl();
        setupCleanGetSubmit();
        setupClearIntercept();
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
    }

    // HTMX hook: runs right before request is sent
    document.body.addEventListener("htmx:configRequest", pruneEmptyParams);
})();