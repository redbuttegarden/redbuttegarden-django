$('#collection-list-table').find('tr td:nth-child(2) a').each(function() {
    let name = $( this ).text();
    let sanitized_name = $('<div>').text(name).html();
    $(this).text(style_full_name(sanitized_name));
});