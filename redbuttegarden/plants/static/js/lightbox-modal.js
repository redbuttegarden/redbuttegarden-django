function openModal() {
    document.getElementById("myModal").style.display = "block";
}

function closeModal(clicked_id) {
    console.log(clicked_id);
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
    const dots = document.getElementsByClassName("demo");
    const captionText = document.getElementById("caption");

    if (n > slides.length) {slideIndex = 1}

    for (i = 0; i < slides.length; i++) {
        slides[i].style.display = "none";
    }
    for (i = 0; i < dots.length; i++) {
        dots[i].className = dots[i].className.replace(" active", "");
    }

    slides[slideIndex - 1].style.display = "block";
    dots[slideIndex - 1].className += " active";
    captionText.innerHTML = dots[slideIndex - 1].alt;
}

document.getElementById("myModal").addEventListener('click', e => {
    if (e.target === e.currentTarget) {
        closeModal();
    }
});
