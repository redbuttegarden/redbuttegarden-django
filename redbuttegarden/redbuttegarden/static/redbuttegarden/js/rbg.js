let alerts = document.getElementsByClassName('alert');
const mainElem = document.getElementById('main');

/*
When an alert is dismissed, the element is completely removed from the page structure.
If a keyboard user dismisses the alert using the close button, their focus will suddenly
be lost and, depending on the browser, reset to the start of the page/document. For this
reason, we recommend including additional JavaScript that listens for the closed.bs.alert
event and programmatically sets focus() to the most appropriate location in the page.

https://getbootstrap.com/docs/5.3/components/alerts/
 */
Array.from(alerts).forEach(alert => {
    alert.addEventListener('closed.bs.alert', (event) => {
        mainElem.focus();
    });
});

if ("serviceWorker" in navigator) {
    console.log("Attempting SW register...");
    let refreshingForServiceWorker = false;
    navigator.serviceWorker.addEventListener("controllerchange", () => {
        if (refreshingForServiceWorker) {
            return;
        }
        refreshingForServiceWorker = true;
        window.location.reload();
    });
    navigator.serviceWorker
        .register("/service-worker.js")
        .then((reg) => {
            console.log("SW registered:", reg.scope);
            reg.update();
        })
        .catch((err) => console.error("SW registration failed:", err));
} else {
    console.log("Service workers not supported in this browser/context");
}

(function () {
    const selector = 'a.species-preview-link, a[href*="/plants/species/"]';
    const speciesPath = /\/plants\/species\/(\d+)\/?$/;
    const cache = new Map();
    let card = null;
    let activeLink = null;
    let hideTimer = null;
    let controller = null;

    function previewUrl(link) {
        if (link.dataset.speciesPreviewUrl) {
            return link.dataset.speciesPreviewUrl;
        }
        const url = new URL(link.href, window.location.origin);
        const match = url.pathname.match(speciesPath);
        return match ? `/plants/species/${match[1]}/preview/` : "";
    }

    function closestSpeciesLink(target) {
        if (!(target instanceof Element)) {
            return null;
        }
        return target.closest(selector);
    }

    function getCard() {
        if (card) {
            return card;
        }

        card = document.createElement("div");
        card.className = "species-preview-card";
        card.hidden = true;
        card.setAttribute("role", "dialog");
        card.setAttribute("aria-live", "polite");
        card.innerHTML = `
            <div class="species-preview-card__media" data-preview-media>
                <div class="species-preview-card__placeholder" aria-hidden="true"></div>
                <img class="species-preview-card__image" data-preview-image alt="" hidden>
            </div>
            <div class="species-preview-card__body">
                <div class="species-preview-card__status" data-preview-status>Loading plant details...</div>
                <div class="species-preview-card__content" data-preview-content hidden>
                    <div class="species-preview-card__common-name" data-preview-common-name></div>
                    <div class="species-preview-card__scientific-name" data-preview-full-name></div>
                    <div class="species-preview-card__family" data-preview-family></div>
                    <dl class="species-preview-card__details" data-preview-details></dl>
                </div>
            </div>
        `;
        card.addEventListener("mouseenter", cancelHide);
        card.addEventListener("mouseleave", scheduleHide);
        document.body.appendChild(card);
        return card;
    }

    function positionCard(link) {
        const preview = getCard();
        const linkRect = link.getBoundingClientRect();
        const previewRect = preview.getBoundingClientRect();
        const spacing = 10;
        let top = linkRect.bottom + spacing + window.scrollY;
        let left = linkRect.left + window.scrollX;

        if (linkRect.bottom + spacing + previewRect.height > window.innerHeight) {
            top = linkRect.top - previewRect.height - spacing + window.scrollY;
        }
        if (linkRect.left + previewRect.width > window.innerWidth - spacing) {
            left = window.innerWidth - previewRect.width - spacing + window.scrollX;
        }

        preview.style.top = `${Math.max(spacing + window.scrollY, top)}px`;
        preview.style.left = `${Math.max(spacing + window.scrollX, left)}px`;
    }

    function setLoading() {
        const preview = getCard();
        preview.classList.remove("species-preview-card--text-only");
        preview.querySelector("[data-preview-status]").hidden = false;
        preview.querySelector("[data-preview-status]").textContent = "Loading plant details...";
        preview.querySelector("[data-preview-content]").hidden = true;
        preview.querySelector("[data-preview-media]").hidden = false;
        preview.querySelector("[data-preview-image]").hidden = true;
        preview.querySelector(".species-preview-card__placeholder").hidden = false;
    }

    function setError() {
        const preview = getCard();
        preview.classList.add("species-preview-card--text-only");
        preview.querySelector("[data-preview-status]").hidden = false;
        preview.querySelector("[data-preview-status]").textContent = "Plant details unavailable.";
        preview.querySelector("[data-preview-content]").hidden = true;
        preview.querySelector("[data-preview-media]").hidden = true;
    }

    function renderPreview(data) {
        const preview = getCard();
        const media = preview.querySelector("[data-preview-media]");
        const image = preview.querySelector("[data-preview-image]");
        const placeholder = preview.querySelector(".species-preview-card__placeholder");
        const details = preview.querySelector("[data-preview-details]");

        preview.querySelector("[data-preview-status]").hidden = true;
        preview.querySelector("[data-preview-content]").hidden = false;
        preview.querySelector("[data-preview-common-name]").textContent = data.vernacular_name || "";
        preview.querySelector("[data-preview-full-name]").textContent = data.full_name || "";
        preview.querySelector("[data-preview-family]").textContent = data.family || "";
        details.replaceChildren();

        (data.details || []).forEach((detail) => {
            const term = document.createElement("dt");
            const description = document.createElement("dd");
            term.textContent = `${detail.label}:`;
            description.textContent = detail.value;
            details.append(term, description);
        });

        if (data.image) {
            preview.classList.remove("species-preview-card--text-only");
            media.hidden = false;
            image.hidden = false;
            image.src = data.image.url;
            image.width = data.image.width;
            image.height = data.image.height;
            image.alt = data.image.alt || "";
            placeholder.hidden = true;
        } else {
            preview.classList.add("species-preview-card--text-only");
            image.removeAttribute("src");
            image.hidden = true;
            placeholder.hidden = true;
            media.hidden = true;
        }
    }

    function cancelHide() {
        if (hideTimer) {
            window.clearTimeout(hideTimer);
            hideTimer = null;
        }
    }

    function scheduleHide() {
        cancelHide();
        hideTimer = window.setTimeout(hidePreview, 120);
    }

    function hidePreview() {
        if (card) {
            card.hidden = true;
        }
        activeLink = null;
        if (controller) {
            controller.abort();
            controller = null;
        }
    }

    async function showPreview(link) {
        const url = previewUrl(link);
        if (!url) {
            return;
        }

        cancelHide();
        activeLink = link;
        setLoading();
        getCard().hidden = false;
        positionCard(link);

        if (cache.has(url)) {
            renderPreview(cache.get(url));
            positionCard(link);
            return;
        }

        if (controller) {
            controller.abort();
        }
        controller = new AbortController();

        try {
            const response = await fetch(url, {
                headers: {"Accept": "application/json"},
                signal: controller.signal,
            });
            if (!response.ok) {
                throw new Error(`Preview request failed: ${response.status}`);
            }
            const data = await response.json();
            cache.set(url, data);
            if (activeLink === link) {
                renderPreview(data);
                positionCard(link);
            }
        } catch (error) {
            if (error.name !== "AbortError" && activeLink === link) {
                setError();
                positionCard(link);
            }
        }
    }

    document.addEventListener("mouseover", (event) => {
        const link = closestSpeciesLink(event.target);
        if (link && previewUrl(link)) {
            showPreview(link);
        }
    });

    document.addEventListener("mouseout", (event) => {
        const link = closestSpeciesLink(event.target);
        if (link && !link.contains(event.relatedTarget)) {
            scheduleHide();
        }
    });

    document.addEventListener("focusin", (event) => {
        const link = closestSpeciesLink(event.target);
        if (link && previewUrl(link)) {
            showPreview(link);
        }
    });

    document.addEventListener("focusout", (event) => {
        if (closestSpeciesLink(event.target)) {
            scheduleHide();
        }
    });

    window.addEventListener("scroll", () => {
        if (activeLink && card && !card.hidden) {
            positionCard(activeLink);
        }
    }, {passive: true});

    window.addEventListener("resize", () => {
        if (activeLink && card && !card.hidden) {
            positionCard(activeLink);
        }
    });
})();
