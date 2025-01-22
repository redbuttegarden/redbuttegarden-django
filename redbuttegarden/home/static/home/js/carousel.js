const myCarouselElement = document.querySelector('#imageCarousel')

const carousel = new bootstrap.Carousel(myCarouselElement, {
  interval: 2000,
  touch: false
}).cycle();
