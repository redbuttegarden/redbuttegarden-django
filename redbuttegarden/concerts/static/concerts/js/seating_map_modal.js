const mapModal = document.getElementById("mapModal");
const modalCaption = document.getElementById("caption-display");
const sponsorTable = document.getElementById("spon-table");
const links = sponsorTable.getElementsByTagName("a");
let mapURL = null;

function getMapURL() {
    for (let i = 0; i < links.length; i++) {
        let url = links[i].href;

        if (url.includes("seating-map")) {
            mapURL = url;
            return;
        }
    }
}

function addMapImage() {
    let map = document.createElement('img');
    map.src = mapURL;
    map.alt = 'Amphitheatre Seating Map';
    mapModal.appendChild(map);
}

function modifyLinks() {
    for (let i = 0; i < links.length; i++) {
        let url = links[i].href;

        if (url.includes("seating-map")) {
            links[i].onclick = function (e) {
                e.preventDefault();
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
    getMapURL();
    addMapImage();
    modifyLinks();
}
