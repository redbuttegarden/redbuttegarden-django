const tables = document.getElementsByTagName('table');
Array.from(tables).forEach(table => {
    table.classList.add('table');
});

const donorMapCells = document.querySelectorAll(".donor-package-tables table td:nth-child(5)");
donorMapCells.forEach(cell => {
    const cellText = cell.textContent.trim();

    if (cellText && !cellText.includes("Location")) {
        const donor_seating_map = document.createElement("a");
        donor_seating_map.setAttribute("href", "/media/images/CDC-VenueMap-2025.original.jpg");
        donor_seating_map.classList.add("red");

        donor_seating_map.innerHTML = cell.innerHTML;
        cell.innerHTML = "";
        cell.appendChild(donor_seating_map);
    }
});

const donorLotCells = document.querySelectorAll(".donor-package-tables table td:nth-child(6)");
donorLotCells.forEach(cell => {
    const cellText = cell.textContent.trim();

    if (cellText && cellText.includes("Donor Lot")) {
        const donor_seating_map = document.createElement("a");
        donor_seating_map.setAttribute("href", "/media/images/CDC-VenueMap-2025.original.jpg");
        donor_seating_map.classList.add("red");

        donor_seating_map.innerHTML = cell.innerHTML;
        cell.innerHTML = "";
        cell.appendChild(donor_seating_map)
    } else if (cellText && cellText.includes("Concert Club Lot")) {
        const concert_club_parking_map = document.createElement("a");
        concert_club_parking_map.setAttribute("href", "/media/original_images/concert-club-parking-map.jpg");
        concert_club_parking_map.classList.add("red");

        concert_club_parking_map.innerHTML = cell.innerHTML;
        cell.innerHTML = "";
        cell.appendChild(concert_club_parking_map)
    }
});
