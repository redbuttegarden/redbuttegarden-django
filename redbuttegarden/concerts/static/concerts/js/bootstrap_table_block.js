$("table").addClass("table table-striped");

const donor_seating_map = document.createElement("a");
donor_seating_map.setAttribute("href", "/media/images/donor-seating-map-2018.original.jpg");

const donor_parking_map = document.createElement("a");
donor_parking_map.setAttribute("href", "/media/images/donor-permit-parking-map.original.jpg");

const concert_club_parking_map = document.createElement("a");
concert_club_parking_map.setAttribute("href", "/media/images/concert-club-parking-map.original.jpg");

$("#spon-table table td:nth-child(3)").each(function() {
    $(this).wrapInner(donor_seating_map);
});

$("#spon-table table td:nth-child(6)").each(function() {
    if (this.innerText.trim() === "Donor Lot") {
        $(this).wrapInner(donor_parking_map);
    } else if (this.innerText.trim() === "Concert Club Lot") {
        $(this).wrapInner(concert_club_parking_map);
    }
});
