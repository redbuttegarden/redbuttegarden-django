const docRegex = /([^/]+(?=.(pdf)))/gm;
const imgRegex = /([^/]+(?=[.][\S]+[.](jpg|png|gif|jpeg)))/gm;

$(document).ready(function () {
    $('.block-document').each(function (i, obj) {
        if( $(this).siblings('.block-image').length ) {
            const docURL = $(this).children().attr("href");
            const docFilename = docURL.match(docRegex)[0];
            console.log(docURL);
            console.log(docFilename);
            const imgURL = $(this).siblings('.block-image').children().attr("src");
            const imgFilename = imgURL.match(imgRegex)[0];
            console.log(imgURL);
            console.log(imgFilename);
            if( docFilename === imgFilename ) {
                $(this).siblings('.block-image').children().wrap("<a href=" + docURL + "></a>");
                $(this).remove();
            }
        }
    });
});
