document.addEventListener('DOMContentLoaded', function () {
    const el = document.getElementById('rbg-nav');
    if (!el) return;
    const url = el.dataset.fragmentUrl;
    if (!url) return;

    // Use fetch with credentials so cookies are sent
    fetch(url, {
        method: 'GET',
        credentials: 'same-origin',
        headers: {
            'Accept': 'text/html'
        }
    }).then(function (resp) {
        if (!resp.ok) throw resp;
        return resp.text();
    }).then(function (html) {
        // Inject fragment HTML
        el.innerHTML = html;

        // Re-initialize Bootstrap collapse toggles to ensure they work after injection
        try {
            var collapseEl = el.querySelector('.collapse');
            if (collapseEl) {
                // If using bootstrap 5, no explicit re-init is required for markup-driven toggles,
                // but ensure event listeners exist by re-attaching toggle buttons if needed.
                // Optionally do nothing; modern bootstrap initializes on click.
            }
        } catch (e) {
            console.warn('nav fragment init error', e);
        }

        // Optionally init search modal or other JS behaviors inside the fragment
    }).catch(function (err) {
        // Keep the skeleton if fragment fails
        console.warn('Failed to fetch nav fragment', err);
    });
});
