const images = document.querySelectorAll('.image-row img');
const leftArrow = document.querySelector('.arrow-left');
const rightArrow = document.querySelector('.arrow-right');
let imageIndex = 0;

rightArrow.addEventListener('click', event => {
    scrollSocialRight(event);
});

leftArrow.addEventListener('click', event => {
    scrollSocialLeft(event);
});

function scrollSocialRight(event) {
    determineImageIndex(event.x, event.y);
    imageIndex++;
    if (imageIndex > images.length) {
        imageIndex = images.length;
    }
    leftArrow.classList.remove('d-none');
    scrollToImage();
}

function scrollSocialLeft(event) {
    determineImageIndex(event.x, event.y);
    imageIndex--;
    if (imageIndex < 0) {
        imageIndex = 0;
    }
    scrollToImage();
}

function nearestImageFromPoint(x, y) {
    let nearestImg = null;
    let minDistance = Infinity;

    images.forEach(img => {
        const rect = img.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        const distance = Math.sqrt((centerX - x) ** 2 + (centerY - y) ** 2);

        if (distance < minDistance) {
            minDistance = distance;
            nearestImg = img;
        }
    });

    return nearestImg;
}

function determineImageIndex(x, y) {
    const imageNearestClick = nearestImageFromPoint(x, y);
    imageIndex = Array.from(images).indexOf(imageNearestClick);
}

function scrollToImage() {
    images[imageIndex].scrollIntoView({block: "nearest", inline: "nearest", behavior: "smooth"});
}
