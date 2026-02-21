/**
 * membership_widget.js
 *
 * Responsibilities:
 *  - attach drag & drop handlers for #priority-list
 *  - maintain hidden weight inputs based on order
 *  - handle move up/down buttons and keyboard interaction
 *  - handle HTMX swap lifecycle for the #suggestions region:
 *      - focus/scroll after swap
 *      - initialize/destroy Bootstrap tooltips inside swapped regions
 *
 * Designed to be idempotent and safe to load/excute multiple times.
 */

const MembershipWidget = (function () {
    const rankToWeight = [10, 6, 2];
    const INIT_FLAG = 'data-membership-widget-initialized';

    // Utility: safely query selector
    function q(el, sel) {
        return el ? el.querySelector(sel) : null;
    }

    /* -------------------------
       Tooltip helpers (Bootstrap)
       ------------------------- */
    function initTooltips(root = document) {
        const triggers = Array.from((root || document).querySelectorAll('[data-bs-toggle="tooltip"]'));
        triggers.forEach((el) => {
            if (bootstrap.Tooltip.getInstance(el)) return;
            new bootstrap.Tooltip(el);
        });
    }

    function destroyTooltips(root = document) {
        const triggers = Array.from((root || document).querySelectorAll('[data-bs-toggle="tooltip"]'));
        triggers.forEach((el) => {
            const inst = bootstrap.Tooltip.getInstance(el);
            if (inst) inst.dispose();
        });
    }

    /* -------------------------
       Priority list behavior
       ------------------------- */
    function updateWeightsFromOrder(list) {
        if (!list) return;
        const items = Array.from(list.querySelectorAll('li[data-key]'));
        items.forEach((item, idx) => {
            const key = item.dataset.key;
            const weight = rankToWeight[idx] || 0;
            if (key === 'admissions') {
                const el = document.getElementById('id_admissions_weight');
                if (el) el.value = weight;
            } else if (key === 'cardholders') {
                const el = document.getElementById('id_cardholders_weight');
                if (el) el.value = weight;
            } else if (key === 'tickets') {
                const el = document.getElementById('id_tickets_weight');
                if (el) el.value = weight;
            }
        });
    }

    let dragSrcEl = null;

    function handleDragStart(e) {
        dragSrcEl = this;
        this.classList.add('dragging');
        this.setAttribute('aria-grabbed', 'true');
        try {
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', this.dataset.key || '');
        } catch (err) {
            // some browsers or contexts may throw; ignore
        }
    }
    function handleDragOver(e) {
        if (e.preventDefault) e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        const list = this._membershipList;
        const target = closestListItem(e.target, list);
        if (!target || target === dragSrcEl) return;
        const rect = target.getBoundingClientRect();
        const next = e.clientY - rect.top > rect.height / 2;
        target.parentNode.insertBefore(dragSrcEl, next ? target.nextSibling : target);
    }
    function handleDragEnd() {
        this.classList.remove('dragging');
        this.setAttribute('aria-grabbed', 'false');
        const list = this._membershipList;
        updateWeightsFromOrder(list);
    }
    function closestListItem(el, list) {
        while (el && el !== list) {
            if (el.matches && el.matches('li[data-key]')) return el;
            el = el.parentNode;
        }
        return null;
    }

    function attachDragHandlers(list) {
        if (!list) return;
        // prevent double-init
        if (list.hasAttribute(INIT_FLAG)) return;
        list.setAttribute(INIT_FLAG, '1');

        const items = list.querySelectorAll('li[data-key]');
        items.forEach((item) => {
            // bind a reference to the parent list for handlers that need it
            item._membershipList = list;

            item.addEventListener('dragstart', handleDragStart, false);
            item.addEventListener('dragover', handleDragOver, false);
            item.addEventListener('dragend', handleDragEnd, false);

            const handle = item.querySelector('.priority-handle');
            if (handle) handle.setAttribute('tabindex', '0');
        });

        // allow dropping on list container
        list.addEventListener(
            'dragover',
            function (e) {
                e.preventDefault();
            },
            false
        );
    }

    function moveItemUp(li) {
        if (li.previousElementSibling) li.parentNode.insertBefore(li, li.previousElementSibling);
    }
    function moveItemDown(li) {
        if (li.nextElementSibling) li.parentNode.insertBefore(li.nextElementSibling, li);
    }

    function attachMoveButtons(list) {
        if (!list) return;
        // guard for double-init
        if (list._moveButtonsAttached) return;
        list._moveButtonsAttached = true;

        list.addEventListener('click', function (e) {
            const up = e.target.closest('.btn-move-up');
            const down = e.target.closest('.btn-move-down');
            if (up || down) {
                const li = e.target.closest('li[data-key]');
                if (!li) return;
                if (up) moveItemUp(li);
                if (down) moveItemDown(li);
                updateWeightsFromOrder(list);
            }
        });

        list.addEventListener('keydown', function (e) {
            const handle = e.target.closest && e.target.closest('.priority-handle');
            if (!handle) return;
            const li = handle.closest('li[data-key]');
            if (!li) return;
            if (e.key === 'ArrowUp') {
                e.preventDefault();
                moveItemUp(li);
                updateWeightsFromOrder(list);
                li.focus();
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                moveItemDown(li);
                updateWeightsFromOrder(list);
                li.focus();
            }
        });
    }

    /* -------------------------
       High level init / lifecycle
       ------------------------- */
    function init(root = document) {
        // Priority list lives in the main document; still allow root to be a swapped node
        const list = root.getElementById ? root.getElementById('priority-list') : root.querySelector('#priority-list');
        if (list) {
            attachDragHandlers(list);
            attachMoveButtons(list);
            updateWeightsFromOrder(list);
        }

        // initialize any tooltips found in the provided root
        initTooltips(root);
    }

    // HTMX hooks: focus/scroll after swap for #suggestions, and tooltip cleanup before swap
    function bindHtmxLifecycle() {
        // guard to avoid multiple binding
        if (bindHtmxLifecycle._bound) return;
        bindHtmxLifecycle._bound = true;

        document.body.addEventListener('htmx:afterSwap', function (event) {
            if (event.detail && event.detail.target && event.detail.target.id === 'suggestions') {
                const el = event.detail.target;
                // Focus & scroll as before
                el.setAttribute('tabindex', '-1');
                el.focus({ preventScroll: true });
                el.scrollIntoView({ behavior: 'smooth', block: 'start' });

                // Init tooltips in the swapped content
                initTooltips(el);

                // If the priority list lives inside the swapped content (rare), init it too
                const possibleList = el.querySelector && el.querySelector('#priority-list');
                if (possibleList) init(possibleList);
            }
        });

        // When HTMX is about to replace content, dispose tooltips inside the target to avoid leaks
        document.body.addEventListener('htmx:beforeSwap', function (event) {
            if (event.detail && event.detail.target) {
                destroyTooltips(event.detail.target);
            }
        });
    }

    /* -------------------------
       Auto-init on DOMContentLoaded
       ------------------------- */
    function autoInit() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function () {
                init(document);
                bindHtmxLifecycle();
            });
        } else {
            init(document);
            bindHtmxLifecycle();
        }
    }

    // Expose public API for testing or manual re-init
    return {
        init,
        initTooltips,
        destroyTooltips,
        autoInit,
    };
})();

(function () {
    function parseIntSafe(el) {
        const n = parseInt(el?.value ?? "0", 10);
        return Number.isFinite(n) ? n : 0;
    }

    function formatTemplate(template, tickets) {
        return template.replaceAll("{tickets}", String(tickets));
    }

    function getJsonScript(id) {
        const el = document.getElementById(id);
        if (!el) return null;
        try {
            return JSON.parse(el.textContent);
        } catch (_) {
            return null;
        }
    }

    const template = getJsonScript("presale-msg-template") || "";
    const enforcedLevelsRaw = getJsonScript("presale-levels") || "2,4,6";
    const enforcedLevels = new Set(
        String(enforcedLevelsRaw)
            .split(",")
            .map((s) => parseInt(s.trim(), 10))
            .filter((n) => Number.isFinite(n))
    );

    function init() {
        const cardholdersEl = document.getElementById("id_cardholders");
        const admissionsEl = document.getElementById("id_admissions");
        const ticketsEl = document.getElementById("id_member_tickets");
        const errorEl = document.getElementById("presale-error");

        if (!cardholdersEl || !admissionsEl || !ticketsEl || !errorEl) return;

        function validatePresaleRule({ report = false } = {}) {
            const cardholders = parseIntSafe(cardholdersEl);
            const admissions = parseIntSafe(admissionsEl);
            const tickets = parseIntSafe(ticketsEl);

            // only enforce for 2/4/6
            if (!enforcedLevels.has(tickets)) {
                errorEl.hidden = true;
                errorEl.textContent = "";
                // clear any custom validity we set
                ticketsEl.setCustomValidity?.("");
                return true;
            }

            const totalPeople = cardholders + admissions;

            if (totalPeople < tickets) {
                const msg = formatTemplate(template, tickets);
                errorEl.textContent = msg;
                errorEl.hidden = false;

                // IMPORTANT: hook into native constraint validation too
                // (so browser/htmx flows can be blocked consistently)
                if (ticketsEl.setCustomValidity) {
                    ticketsEl.setCustomValidity(msg);
                    if (report && ticketsEl.reportValidity) ticketsEl.reportValidity();
                }

                return false;
            }

            errorEl.hidden = true;
            errorEl.textContent = "";
            ticketsEl.setCustomValidity?.("");
            return true;
        }

        ["input", "change"].forEach((evt) => {
            cardholdersEl.addEventListener(evt, () => validatePresaleRule());
            admissionsEl.addEventListener(evt, () => validatePresaleRule());
            ticketsEl.addEventListener(evt, () => validatePresaleRule());
        });

        validatePresaleRule();

        const formEl = ticketsEl.closest("form");
        if (formEl) {
            // Normal submit path
            formEl.addEventListener("submit", function (e) {
                if (!validatePresaleRule({ report: true })) {
                    e.preventDefault();
                    ticketsEl.focus();
                }
            });

            // HTMX submit path (blocks hx-post requests too)
            formEl.addEventListener("htmx:beforeRequest", function (e) {
                if (!validatePresaleRule({ report: true })) {
                    e.preventDefault(); // stops the htmx request
                    ticketsEl.focus();
                }
            });
        }
    }

    // init once on load
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

    // and re-init after htmx swaps content (Fix 2 below)
    document.body.addEventListener("htmx:afterSwap", init);
})();



// Auto-run
MembershipWidget.autoInit();
