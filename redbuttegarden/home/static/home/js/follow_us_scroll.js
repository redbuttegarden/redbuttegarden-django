const row = document.querySelector('.image-row');

function scrollSocialRight() {
    const leftArrow = document.querySelector('.arrow-left');
    leftArrow.classList.remove('d-none');
    row.scrollBy({left: 400, behavior: 'smooth'});
}

function scrollSocialLeft() {
    row.scrollBy({left: -400, behavior: 'smooth'});
}
