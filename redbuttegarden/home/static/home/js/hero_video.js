const videoElem = document.getElementById('heroVideo');
const imageSlideshowElem = document.getElementById('imageCarousel');

function toggleVisibility(event) {
    videoElem.classList.toggle('d-none');
    console.log(imageSlideshowElem.classList);
    imageSlideshowElem.classList.toggle('d-none');
    console.log(imageSlideshowElem.classList);
}

videoElem.addEventListener('ended', toggleVisibility);