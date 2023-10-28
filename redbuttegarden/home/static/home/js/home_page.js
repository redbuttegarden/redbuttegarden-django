const carouselElement = document.getElementById('homePageCarousel');
const slideShowPauseButton = document.getElementById("pause-btn");

const carousel = bootstrap.Carousel.getOrCreateInstance(carouselElement);
let paused = false;

slideShowPauseButton.addEventListener('click', toggleSlideShow);
carouselElement.addEventListener('mouseenter', function () {
    // Pause unless overridden by paused variable controlled by button click
    if (!paused) {
        carousel.pause();
    }
});
carouselElement.addEventListener('mouseleave', function () {
    if (!paused) {
        carousel.cycle();
    }
});

function toggleSlideShow() {
    const button_text = slideShowPauseButton.textContent || slideShowPauseButton.innerText;

    if (button_text === "Pause Slideshow") {
        carousel.pause();
        slideShowPauseButton.textContent = "Resume Slideshow";
        paused = true;
    } else {
        carousel.cycle();
        carousel.next();
        slideShowPauseButton.textContent = "Pause Slideshow";
        paused = false;
    }
}
