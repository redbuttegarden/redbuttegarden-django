/**
 * Enhance a dedication image gallery with an accessible Bootstrap photo viewer.
 */
document.addEventListener("DOMContentLoaded", () => {
    const gallery = document.querySelector("[data-dedication-gallery]");
    const modalElement = document.getElementById("dedication-gallery-modal");

    if (!gallery || !modalElement || !window.bootstrap) return;

    const slides = Array.from(modalElement.querySelectorAll("[data-gallery-slide]"));
    const thumbnailButtons = Array.from(
        modalElement.querySelectorAll(".dedication-gallery-modal__thumbnail"),
    );
    const caption = modalElement.querySelector("[data-gallery-caption]");
    const copyright = modalElement.querySelector("[data-gallery-copyright]");
    const count = modalElement.querySelector("[data-gallery-count]");
    const status = modalElement.querySelector("[data-gallery-status]");
    const previous = modalElement.querySelector("[data-gallery-previous]");
    const next = modalElement.querySelector("[data-gallery-next]");
    const closeButton = modalElement.querySelector("[data-bs-dismiss='modal']");
    const modal = window.bootstrap.Modal.getOrCreateInstance(modalElement);
    let selectedIndex = 0;
    let triggeringButton = null;

    if (
        !slides.length ||
        !thumbnailButtons.length ||
        !caption ||
        !copyright ||
        !count ||
        !status ||
        !previous ||
        !next ||
        !closeButton
    ) {
        return;
    }

    /** Show one photo and update the modal's safe text-only metadata. */
    function selectPhoto(index) {
        selectedIndex = (index + slides.length) % slides.length;
        const selectedThumbnail = thumbnailButtons[selectedIndex];

        slides.forEach((slide, slideIndex) => {
            slide.hidden = slideIndex !== selectedIndex;
        });
        thumbnailButtons.forEach((thumbnail, thumbnailIndex) => {
            thumbnail.setAttribute(
                "aria-current",
                String(thumbnailIndex === selectedIndex),
            );
        });

        caption.textContent = selectedThumbnail.dataset.galleryCaption || "";
        caption.hidden = !caption.textContent;
        copyright.textContent = selectedThumbnail.dataset.galleryCopyright || "";
        copyright.hidden = !copyright.textContent;
        count.textContent = `${selectedIndex + 1} of ${slides.length}`;
        status.textContent = `Showing photo ${selectedIndex + 1} of ${slides.length}`;
    }

    function openPhoto(index, trigger) {
        selectPhoto(index);
        triggeringButton = trigger;
        modal.show();
    }

    gallery.querySelectorAll("[data-gallery-index]").forEach((button) => {
        button.addEventListener("click", () => {
            openPhoto(Number(button.dataset.galleryIndex), button);
        });
    });
    thumbnailButtons.forEach((button) => {
        button.addEventListener("click", () => {
            selectPhoto(Number(button.dataset.galleryIndex));
        });
    });
    previous.addEventListener("click", () => selectPhoto(selectedIndex - 1));
    next.addEventListener("click", () => selectPhoto(selectedIndex + 1));
    modalElement.addEventListener("keydown", (event) => {
        if (event.key === "ArrowLeft") {
            event.preventDefault();
            selectPhoto(selectedIndex - 1);
        }
        if (event.key === "ArrowRight") {
            event.preventDefault();
            selectPhoto(selectedIndex + 1);
        }
    });
    modalElement.addEventListener("shown.bs.modal", () => {
        window.setTimeout(() => closeButton.focus(), 50);
    });
    modalElement.addEventListener("hidden.bs.modal", () => {
        const trigger = triggeringButton;
        triggeringButton = null;

        window.setTimeout(() => {
            if (trigger && trigger.isConnected && !trigger.disabled) {
                trigger.focus();
            }
        }, 50);
    });

    selectPhoto(0);
});
