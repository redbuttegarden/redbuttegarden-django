const images = document.querySelectorAll(".image-row img");
const leftArrow = document.querySelector(".arrow-left");
const rightArrow = document.querySelector(".arrow-right");
let imageIndex = 0;

if (rightArrow && leftArrow && images.length) {
    rightArrow.addEventListener("click", (event) => {
        scrollSocialRight(event);
    });

    leftArrow.addEventListener("click", (event) => {
        scrollSocialLeft(event);
    });
}

/**
 * Scroll the gallery one image to the right.
 *
 * @param {MouseEvent} event - Activating click; keyboard clicks have no pointer coordinates.
 */
function scrollSocialRight(event) {
    determineImageIndex(event);
    imageIndex++;
    if (imageIndex >= images.length) {
        imageIndex = images.length - 1;
    }
    leftArrow.classList.remove("d-none");
    scrollToImage();
}

/**
 * Scroll the gallery one image to the left.
 *
 * @param {MouseEvent} event - Activating click; keyboard clicks have no pointer coordinates.
 */
function scrollSocialLeft(event) {
    determineImageIndex(event);
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

/**
 * Align the carousel index with a pointer click without disrupting keyboard use.
 *
 * @param {MouseEvent} event - The button activation event.
 */
function determineImageIndex(event) {
    if (event.detail === 0) return;
    if (!Number.isFinite(event.clientX) || !Number.isFinite(event.clientY)) return;

    const imageNearestClick = nearestImageFromPoint(event.clientX, event.clientY);
    const nearestIndex = Array.from(images).indexOf(imageNearestClick);
    if (nearestIndex >= 0) imageIndex = nearestIndex;
}

/** Scroll the selected gallery image into view. */
function scrollToImage() {
    const image = images[imageIndex];
    if (!image) return;
    image.scrollIntoView({block: "nearest", inline: "nearest", behavior: "smooth"});
}
