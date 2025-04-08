const videoElem = document.getElementById('heroVideo');
const imageSlideshowElem = document.getElementById('imageCarousel');

function toggleVisibility(event) {
    videoElem.parentElement.classList.toggle('d-none');
    imageSlideshowElem.classList.toggle('d-none');
}

videoElem.addEventListener('ended', toggleVisibility);