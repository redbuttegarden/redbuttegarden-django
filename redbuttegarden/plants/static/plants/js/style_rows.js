$('#collection-list-table').find('tr td:nth-child(2) a').each(function() {
    let name = $( this ).text();
    $( this ).html(style_full_name(name));
});