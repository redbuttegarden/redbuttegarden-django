document.addEventListener('DOMContentLoaded', function () {
    const speciesElem = document.querySelector('#id_species');
    const collectionsElem = document.querySelector('#id_collections');

    if (speciesElem && collectionsElem) {
        speciesElem.addEventListener('change', function () {
            const speciesSelected = speciesElem.value;

            // Example: Fetch new options via AJAX
            fetch(`/plants/admin/snippets/filtered_collections/${speciesSelected}/`)
                .then(response => response.json())
                .then(data => {
                    // Clear existing options
                    collectionsElem.innerHTML = '';

                    // Populate new options
                    data.options.forEach(opt => {
                        const option = document.createElement('option');
                        option.value = opt.value;
                        option.textContent = opt.label;
                        collectionsElem.appendChild(option);
                    });
                });
        });
    }
});
