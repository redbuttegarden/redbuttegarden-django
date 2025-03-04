const mapModal = document.getElementById("mapModal");
const modalCaption = document.getElementById("caption-display");
const links = document.getElementsByTagName("a");
const seatingMapURL = "/media/images/CDC-VenueMap-2025.original.jpg";
const donorParkingMapURL = "/media/original_images/donor-permit-parking-map.jpg";
const concertClubParkingMapURL = "/media/original_images/concert-club-parking-map.jpg";

function createSeatingMapImage() {
    let map = document.createElement('img');
    map.src = seatingMapURL;
    map.alt = 'Amphitheatre Seating Map';
    return map;
}

function createDonorParkingMapImage() {
    let map = document.createElement('img');
    map.src = donorParkingMapURL;
    map.alt = 'Donor Parking Map';
    return map;
}

function createConcertClubParkingMapImage() {
    let map = document.createElement('img');
    map.src = concertClubParkingMapURL;
    map.alt = 'Concert Club Parking Map';
    return map;
}

function addMapImage(map) {
    mapModal.appendChild(map);
}

function removeMapImage() {
    while (mapModal.firstChild) {
        mapModal.removeChild(mapModal.firstChild);
    }
}

function modifyLinks(seatingMap, donorParkingMap, concertClubParkingMap) {
    for (let i = 0; i < links.length; i++) {
        let url = links[i].href;

        if (url.includes("seating-map")) {
            links[i].onclick = function (e) {
                e.preventDefault();
                removeMapImage();
                addMapImage(seatingMap);
                openModal();
                let target, text;
                target = e.target;
                text = target.textContent || target.innerText;
                modalCaption.innerText = text;
            }
        } else if (url.includes("donor-permit-parking-map")) {
            links[i].onclick = function (e) {
                e.preventDefault();
                removeMapImage();
                addMapImage(donorParkingMap);
                openModal();
                let target, text;
                target = e.target;
                text = target.textContent || target.innerText;
                modalCaption.innerText = text;
            }
        } else if (url.includes("concert-club-parking-map")) {
            links[i].onclick = function (e) {
                e.preventDefault();
                removeMapImage();
                addMapImage(concertClubParkingMap);
                openModal();
                let target, text;
                target = e.target;
                text = target.textContent || target.innerText;
                modalCaption.innerText = text;
            }
        }
    }
}

window.onload = function () {
    let seatingMap = createSeatingMapImage();
    let donorParkingMap = createDonorParkingMapImage();
    let concertClubParkingMap = createConcertClubParkingMapImage();
    modifyLinks(seatingMap, donorParkingMap, concertClubParkingMap);
}
