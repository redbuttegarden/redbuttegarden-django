const row = document.querySelector('.image-row');
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

function determineImageIndex(x, y) {
    const imageUnderClick = document.elementsFromPoint(x, y).find(element => element.tagName === 'IMG');
    imageIndex = Array.from(images).indexOf(imageUnderClick);
}

function scrollToImage() {
    images[imageIndex].scrollIntoView({block: "nearest", inline: "nearest", behavior: "smooth"});
}
