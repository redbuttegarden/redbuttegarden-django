const docRegex = /([^/]+(?=.(pdf)))/gm;
const imgRegex = /([^/]+(?=[.][\S]+[.](jpg|png|gif|jpeg)))/gm;

document.addEventListener('DOMContentLoaded', function () {
    const documentBlocks = document.querySelectorAll('.block-document');

    documentBlocks.forEach(function (blockDocument) {
        // Find sibling .block-image
        const blockImage = blockDocument.parentElement.querySelector('.block-image');

        if (!blockImage) return;

        const docLink = blockDocument.querySelector('a');
        const img = blockImage.querySelector('img');

        if (!docLink || !img) return;

        const docURL = docLink.getAttribute('href');
        const docMatch = docURL.match(docRegex);
        if (!docMatch) return;

        const docFilename = docMatch[0];

        const imgURL = img.getAttribute('src');
        const imgMatch = imgURL.match(imgRegex);
        if (!imgMatch) return;

        const imgFilename = imgMatch[0];

        console.log(docURL);
        console.log(docFilename);
        console.log(imgURL);
        console.log(imgFilename);

        if (docFilename === imgFilename) {
            // Wrap image in link
            const link = document.createElement('a');
            link.href = docURL;

            img.parentNode.insertBefore(link, img);
            link.appendChild(img);

            // Remove the document block
            blockDocument.remove();
        }
    });
});
