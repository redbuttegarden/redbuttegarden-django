function style_full_name(name) {
    let parts = name.split(" ");

    for (let i = 0; i < parts.length; i++) {
        if (typeof parts[i + 1] != 'undefined' && parts[i][0] === "'") {
            parts[i] = '</span><span>' + parts[i] + ' ' + parts[i + 1];
            parts.splice(i + 1, 1);
        } else if (parts[i][0] === "'" && parts[i][parts[i].length - 1] === "'") {
            parts[i] = '</span><span>' + parts[i];
        } else if (parts[i] === 'var.' || parts[i] === 'subsp.' || parts[i] === 'f.') {
            parts[i] = '</span>' + parts[i] + '<span class="fst-italic">';
        }
    }

    parts.splice(0, 0, '<span class="fst-italic">');
    parts.splice(parts.length, 0, '</span>');

    return parts.join(" ");
}
