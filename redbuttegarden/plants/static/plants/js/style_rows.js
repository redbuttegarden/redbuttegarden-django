document.querySelectorAll('#collection-list-table tr td:nth-child(2) a').forEach(function(element) {
    let name = element.textContent;
    let sanitized_name = new DOMParser().parseFromString(name, 'text/html').body.textContent;
    element.innerHTML = style_full_name(sanitized_name);
});