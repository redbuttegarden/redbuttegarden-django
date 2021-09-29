function openModal() {
    document.getElementById("myModal").style.display = "block";
}

function closeModal(clicked_id) {
    document.getElementById("myModal").style.display = "none";
}

let slideIndex = 1;
showSlides(slideIndex);

function plusSlides(n) {
    showSlides(slideIndex += n);
}

function currentSlide(n) {
    showSlides(slideIndex = n);
}

function showSlides(n) {
    let i;
    const slides = document.getElementsByClassName("mySlides");
    const images = document.getElementsByClassName("demo");
    const copyrightText = document.getElementsByClassName("copyright-text");
    const copyrightDisplay = document.getElementById("copyright-display");

    if (n > slides.length) {slideIndex = 1}

    for (i = 0; i < slides.length; i++) {
        slides[i].style.display = "none";
    }
    for (i = 0; i < images.length; i++) {
        images[i].className = images[i].className.replace(" active", "");
    }

    slides[slideIndex - 1].style.display = "block";
    images[slideIndex - 1].className += " active";
    copyrightDisplay.innerHTML = copyrightText[slideIndex - 1].innerHTML;
}

document.getElementById("myModal").addEventListener('click', e => {
    if (e.target === e.currentTarget) {
        closeModal();
    }
});
