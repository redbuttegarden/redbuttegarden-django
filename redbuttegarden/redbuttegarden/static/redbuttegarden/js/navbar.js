function initNavbar() {
    const navbarCollapse = document.querySelector('nav .navbar-collapse');
    if (!navbarCollapse) return;

    const navItemIcons = document.querySelectorAll('#navLinks i.bi');

    function toggleIcons() {
        navItemIcons.forEach(icon => {
            icon.classList.toggle('bi-chevron-down');
            icon.classList.toggle('bi-plus');
            icon.classList.toggle('float-end');
        });
    }

    navbarCollapse.addEventListener('show.bs.collapse', toggleIcons);
    navbarCollapse.addEventListener('hidden.bs.collapse', toggleIcons);
}

// Expose globally so nav-fragment.js can call it
window.initNavbar = initNavbar;
