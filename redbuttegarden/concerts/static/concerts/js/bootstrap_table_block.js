$("table").addClass("table table-striped");

const donor_seating_map = document.createElement("a");
donor_seating_map.setAttribute("href", "/media/original_images/donor-seating-map-2018.jpg");

const donor_parking_map = document.createElement("a");
donor_parking_map.setAttribute("href", "/media/original_images/donor-permit-parking-map.jpg");

const concert_club_parking_map = document.createElement("a");
concert_club_parking_map.setAttribute("href", "/media/original_images/concert-club-parking-map.jpg");

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
    if (text && !text.includes("Seating Location")) {
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