const row = document.querySelector('.image-row');

function scrollSocialRight() {
    console.log('scrolling right');
    const leftArrow = document.querySelector('.arrow-left');
    leftArrow.classList.remove('d-none');
    row.scrollBy({left: 400, behavior: 'smooth'});
}

function scrollSocialLeft() {
    console.log('scrolling left');
    row.scrollBy({left: -400, behavior: 'smooth'});
}
