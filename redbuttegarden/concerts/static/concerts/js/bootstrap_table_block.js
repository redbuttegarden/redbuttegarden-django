$("table").addClass("table");

const donor_seating_map = document.createElement("a");
donor_seating_map.setAttribute("href", "/media/original_images/donor-seating-map-2018.jpg");
donor_seating_map.classList.add("red");

const donor_parking_map = document.createElement("a");
donor_parking_map.setAttribute("href", "/media/original_images/donor-permit-parking-map.jpg");
donor_parking_map.classList.add("red");

const concert_club_parking_map = document.createElement("a");
concert_club_parking_map.setAttribute("href", "/media/original_images/concert-club-parking-map.jpg");
concert_club_parking_map.classList.add("red");

/* Add links to Package Comparison drop-down tables */
$("#spon-table table td:nth-child(3)").each(function() {
    $(this).wrapInner(donor_seating_map);
});

$("#spon-table table td:nth-child(5)").each(function() {
    if (this.innerText.trim() === "Donor Lot") {
        $(this).wrapInner(donor_parking_map);
    } else if (this.innerText.trim() === "Concert Club Lot") {
        $(this).wrapInner(concert_club_parking_map);
    }
});

/* Add links to donor package seating tables */
$(".donor-package-tables table td:nth-child(5)").each(function() {
    let text = this.innerText.trim();
    if (text && !text.includes("Location")) {
        $(this).wrapInner(donor_seating_map);
    }
});

$(".donor-package-tables table td:nth-child(6)").each(function() {
    if (this.innerText.trim().includes("Donor Lot")) {
        $(this).wrapInner(donor_parking_map);
    } else if (this.innerText.trim().includes("Concert Club Lot")) {
        $(this).wrapInner(concert_club_parking_map);
    }
});

/* Italicize "Charitable Gift Portion" text */
$(".donor-package-tables table tr th").each(function() {
    if (this.innerText.trim() === "Charitable Gift Portion") {
        this.classList.add("font-italic");
    }
});
