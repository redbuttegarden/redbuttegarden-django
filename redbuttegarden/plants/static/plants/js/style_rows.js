// Specify the column name you want to target
const targetColumnName = "Full Name"; // Change this to your column header text

// Find the index of the column with that name
const headers = document.querySelectorAll('#collection-list-table th');
let columnIndex = -1;

headers.forEach((header, index) => {
    if (header.textContent.trim() === targetColumnName) {
        columnIndex = index + 1; // nth-child is 1-based
    }
});

if (columnIndex !== -1) {
    // Select all links in that column
    document.querySelectorAll(`#collection-list-table tr td:nth-child(${columnIndex}) a`)
        .forEach(function(element) {
            let name = element.textContent;
            let sanitized_name = new DOMParser().parseFromString(name, 'text/html').body.textContent;
            element.innerHTML = style_full_name(sanitized_name);
        });
} else {
    console.warn(`Column "${targetColumnName}" not found.`);
}
