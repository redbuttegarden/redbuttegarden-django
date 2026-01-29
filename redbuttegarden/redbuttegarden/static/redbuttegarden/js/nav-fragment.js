document.addEventListener('DOMContentLoaded', function () {
    const el = document.getElementById('rbg-nav');
    if (!el) return;

    const url = el.dataset.fragmentUrl;
    if (!url) return;

    fetch(url, {
        method: 'GET',
        credentials: 'same-origin',
        headers: { 'Accept': 'text/html' }
    })
        .then(resp => resp.ok ? resp.text() : Promise.reject(resp.status))
        .then(function (html) {
            el.innerHTML = html;

            el.innerHTML = html;

            // Initialize bootstrap components inside the fragment (idempotent)
            if (window.bootstrap) {
                // Initialize collapse instances
                el.querySelectorAll('.collapse').forEach(collapseEl => {
                    if (!collapseEl.dataset.bsInitialized) {
                        new bootstrap.Collapse(collapseEl, { toggle: false });
                        collapseEl.dataset.bsInitialized = 'true';
                    }
                });

                // Initialize modal(s) - do not auto-show them
                el.querySelectorAll('.modal').forEach(modalEl => {
                    if (!modalEl.dataset.bsInitializedModal) {
                        // create instance but don't show
                        new bootstrap.Modal(modalEl, {});
                        modalEl.dataset.bsInitializedModal = 'true';
                    }
                });

                // Init dropdowns optionally
                el.querySelectorAll('[data-bs-toggle="dropdown"]').forEach(dd => {
                    if (!dd.dataset.bsDropdownInit) {
                        new bootstrap.Dropdown(dd);
                        dd.dataset.bsDropdownInit = 'true';
                    }
                });
            }

            // Call initializers (navbar + search), if present
            if (window.initNavbar) window.initNavbar();
            if (window.initSearch) window.initSearch();
        })
        .catch(err => {
            console.warn('Failed to load nav fragment', err);
        });
});
