const navbarCollapse = document.querySelector('nav .navbar-collapse');
const navItemIcons = document.querySelectorAll('#navLinks i.bi');

navbarCollapse.addEventListener('show.bs.collapse', event => {
    toggleIcons();
});

navbarCollapse.addEventListener('hidden.bs.collapse', event => {
    toggleIcons();
});

function toggleIcons() {
    navItemIcons.forEach(icon => {
        icon.classList.toggle('bi-chevron-down');
        icon.classList.toggle('bi-plus');
        icon.classList.toggle('float-end');
    });
}