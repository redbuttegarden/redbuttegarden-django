const navSearchInput = document.querySelector('#navSearch input[type="search"]');
const searchModalInput = document.querySelector('#searchModalForm input[type="search"]');
const searchModal = new bootstrap.Modal(document.getElementById('searchModal'));
const searchModalSearchButton = document.querySelector('#searchModal button.btn-primary');
const resultsContainer = document.querySelector('#searchResults');
const paginationContainer = document.getElementById('searchModalPaginationContainer');

navSearchInput.addEventListener('focus', (e) => {
    e.preventDefault();
    searchModal.show();
    const searchTerm = searchModalInput.value;
    if (searchTerm.length > 2) { // Only send request if search term has at least 3 characters
        fetchResults(searchTerm, 1);
    }
});

searchModalInput.addEventListener('input', function () {
    const searchTerm = this.value;
    navSearchInput.value = searchTerm;

    if (searchTerm.length > 2) { // Only send request if search term has at least 3 characters
        fetchResults(searchTerm, 1);
    }
});

searchModalSearchButton.addEventListener('click', function () {
    const searchTerm = searchModalInput.value;

    window.location.href = `/search/?q=${searchTerm}`;
});

function fetchResults(query, page) {
    fetch(`/search/?q=${query}&page=${page}`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
        .then(response => response.json())
        .then(data => {
            resultsContainer.innerHTML = '';
            data.results.forEach(result => {
                const resultItem = document.createElement('div');
                resultItem.classList.add('my-2');
                resultItem.innerHTML = `<a href="${result.url}">${result.title}</a>`;
                resultsContainer.appendChild(resultItem);
            });
            paginationContainer.innerHTML = '';

            for (let i = 1; i <= data.pages; i++) {
                const pageLink = document.createElement('a');
                if (i === page) {
                    pageLink.classList.add('selected');
                }
                pageLink.href = '/search/?q=' + encodeURIComponent(query) + '&page=' + i;
                pageLink.textContent = i.toString();
                pageLink.addEventListener('click', function (event) {
                    event.preventDefault();
                    fetchResults(query, i);
                });
                paginationContainer.appendChild(pageLink);
            }
        });
}
