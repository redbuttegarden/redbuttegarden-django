const targetColumnName = "Full Name";

const HTML_ENTITIES = Object.freeze({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
});

/**
 * Escape plain text before it is included in an HTML string.
 */
function escapeHtml(value) {
    // Each original HTML metacharacter is encoded exactly once.
    return String(value ?? "").replace(
        /[&<>"']/g,
        (character) => HTML_ENTITIES[character],
    );
}

/**
 * Produce controlled taxonomic markup from a plain-text plant name.
 */
function style_full_name(plainName) {
    // Escape before examining the name or adding formatting tags. This prevents
    // name-derived text from creating elements, attributes, or event handlers.
    const escapedName = escapeHtml(plainName);

    // Apostrophes are now represented as &#39;. A whitespace-delimited
    // apostrophe marks the cultivar suffix, which should not be italicized.
    const cultivarMatch = escapedName.match(
        /^([\s\S]*?)(\s+&#39;[\s\S]*)$/u,
    );

    const taxonomicName = cultivarMatch
        ? cultivarMatch[1]
        : escapedName;
    const cultivarSuffix = cultivarMatch
        ? cultivarMatch[2]
        : "";

    // Rank indicators remain roman. The capture can only contain one of these
    // fixed, allowlisted values; all other content was escaped above.
    const formattedTaxonomicName = taxonomicName.replace(
        /\s+(subsp\.|subvar\.|subf\.|var\.|f\.)\s+/gu,
        "</i> $1 <i>",
    );

    // The only actual HTML introduced is the application-owned <i> markup.
    return `<i>${formattedTaxonomicName}</i>${cultivarSuffix}`;
}

const table = document.querySelector("#collection-list-table");

if (!table) {
    // Guard against pages where the table is not present.
    console.warn('Table "#collection-list-table" not found.');
} else {
    // Convert the static NodeList once. findIndex stops at the first exact
    // header match instead of scanning every header with a mutable sentinel.
    const columnIndex = Array.from(table.querySelectorAll("th")).findIndex(
        (header) => header.textContent.trim() === targetColumnName,
    );

    if (columnIndex === -1) {
        console.warn(`Column "${targetColumnName}" not found.`);
    } else {
        // findIndex is zero-based; nth-child is one-based. Keeping the query
        // scoped to the table avoids searching unrelated page content.
        const selector = `tr td:nth-child(${columnIndex + 1}) a`;

        table.querySelectorAll(selector).forEach((link) => {
            // textContent reads plain text without invoking an HTML parser.
            // innerHTML is safe at this controlled boundary because the
            // formatter escapes all variable content and emits only fixed tags.
            // Updating only the children preserves href, ARIA attributes,
            // event listeners, focus behavior, and the anchor itself.
            link.innerHTML = style_full_name(link.textContent);
        });
    }
}
