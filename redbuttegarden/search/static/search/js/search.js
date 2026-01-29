function initSearch() {
    // avoid double-init
    if (window._rbg_search_initialized) return;
    window._rbg_search_initialized = true;

    // Query DOM elements (may be in injected fragment)
    const navSearchForm = document.getElementById('navSearch');
    const navSearchInput = document.querySelector('#navSearch input[type="search"]');
    const searchModalEl = document.getElementById('searchModal');
    const searchModalInput = document.querySelector('#searchModalForm input[type="search"]');
    const searchModalSearchButton = document.querySelector('#searchModal button.btn-primary');
    const resultsContainer = document.querySelector('#searchResults');
    const paginationContainer = document.getElementById('searchModalPaginationContainer');

    // If the modal element isn't present yet, bail (caller should re-call initSearch when it is).
    if (!searchModalEl) return;

    // Create/obtain a Bootstrap Modal instance (idempotent)
    let searchModal = null;
    if (window.bootstrap && window.bootstrap.Modal) {
        // If already created, reuse it
        searchModal = bootstrap.Modal.getInstance(searchModalEl) || new bootstrap.Modal(searchModalEl, {});
    }

    // Defensive: check elements required for behavior, fallback gracefully
    if (navSearchForm) {
        navSearchForm.addEventListener('click', (e) => {
            e.preventDefault();
            if (searchModal) searchModal.show();
            const searchTerm = (searchModalInput && searchModalInput.value) || '';
            if (searchTerm.length > 2) fetchResults(searchTerm, 1);
        });
    }

    if (navSearchInput) {
        navSearchInput.addEventListener('focus', (e) => {
            e.preventDefault();
            if (searchModal) searchModal.show();
            const searchTerm = (searchModalInput && searchModalInput.value) || '';
            if (searchTerm.length > 2) fetchResults(searchTerm, 1);
        });
    }

    if (searchModalInput) {
        searchModalInput.addEventListener('input', function () {
            const searchTerm = this.value;
            if (navSearchInput) navSearchInput.value = searchTerm;
            if (searchTerm.length > 2) fetchResults(searchTerm, 1);
        });
    }

    if (searchModalSearchButton) {
        searchModalSearchButton.addEventListener('click', function () {
            const searchTerm = (searchModalInput && searchModalInput.value) || '';
            window.location.href = `/search/?q=${encodeURIComponent(searchTerm)}`;
        });
    }

    // Helper used by the handlers above (keep outside to share)
    function fetchResults(query, page) {
        if (!resultsContainer || !paginationContainer) return;

        fetch(`/search/?q=${encodeURIComponent(query)}&page=${page}`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
            .then(response => response.json())
            .then(data => {
                resultsContainer.innerHTML = '';
                (data.results || []).forEach(result => {
                    const resultItem = document.createElement('div');
                    resultItem.classList.add('my-2');
                    resultItem.innerHTML = `<a href="${result.url}">${result.title}</a>`;
                    resultsContainer.appendChild(resultItem);
                });

                paginationContainer.innerHTML = '';
                for (let i = 1; i <= (data.pages || 1); i++) {
                    const pageLink = document.createElement('a');
                    if (i === page) pageLink.classList.add('selected');
                    pageLink.href = '/search/?q=' + encodeURIComponent(query) + '&page=' + i;
                    pageLink.textContent = i.toString();
                    pageLink.addEventListener('click', function (event) {
                        event.preventDefault();
                        fetchResults(query, i);
                    });
                    paginationContainer.appendChild(pageLink);
                }
            })
            .catch(err => {
                console.warn('Search fetch error', err);
            });
    }
}

// expose the initializer
window.initSearch = initSearch;
