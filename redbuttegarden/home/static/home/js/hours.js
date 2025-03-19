const hoursData = JSON.parse(document.getElementById('hours-data').textContent);
const hoursElem = document.getElementById('hours');
const visitTextElem = document.getElementById('visitText');
const emphaticTextElem = document.getElementById('emphaticText');
let concertDay = false;

// Convert open times into string to be shown on home page
function processGardenHours(garden_open, garden_close) {
    let openTime = garden_open.split(":");
    let closeTime = garden_close.split(":");
    let openHour = parseInt(openTime[0]);
    let closeHour = parseInt(closeTime[0]);
    let openMinute = parseInt(openTime[1]);
    let closeMinute = parseInt(closeTime[1]);

    let currentDate = new Date()

    let openDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate(), openHour, openMinute);
    let closeDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate(), closeHour, closeMinute);

    let openTimeStr;
    let closeTimeStr;
    if (openMinute !== 0) {
        openTimeStr = openHour > 12 ? (openHour - 12) + ":" + openMinute.toString().padStart(2, "0") + " PM" : openHour + ":" + openMinute.toString().padStart(2, "0") + " AM";
    } else {
        openTimeStr = openHour > 12 ? (openHour - 12) + " PM" : openHour + " AM";
    }

    if (closeMinute !== 0) {
        closeTimeStr = closeHour > 12 ? (closeHour - 12) + ":" + closeMinute.toString().padStart(2, "0") + " PM" : closeHour + ":" + closeMinute.toString().padStart(2, "0") + " AM";
    } else {
        closeTimeStr = closeHour > 12 ? (closeHour - 12) + " PM" : closeHour + " AM";
    }

    return {
        openDate: openDate,
        closeDate: closeDate,
        openTimeStr: openTimeStr,
        closeTimeStr: closeTimeStr
    }
}

function setHours(date = new Date()) {
    let offset = date.getTimezoneOffset() / 60;
    let offsetDifference = offset - 6;

    let currentMonth = date.getMonth() + 1;
    let currentDay = date.getDate();
    let currentHour = date.getHours() + offsetDifference;
    let currentMinute = date.getMinutes();
    let minutesBeforeOpeningOrClosing = 60 - currentMinute;

    let processed_times = processGardenHours(hoursData.garden_open, hoursData.garden_close);

    if (hoursData && !concertDay) {
        hoursElem.textContent = processed_times.openTimeStr + " - " + processed_times.closeTimeStr;
        visitTextElem.textContent = hoursData.additional_message;
        emphaticTextElem.textContent = hoursData.additional_emphatic_mesg;
    }
    displayOpenClosed(processed_times);
    handleConcertDay(currentMonth, currentDay, currentHour, minutesBeforeOpeningOrClosing);
}

// Display open or closed icon/bubble over the "Visit the garden" image
function displayOpenClosed(timeInfoDict) {
    const visitGardenImgContainer = document.getElementById('visitInfoImg');
    let openClosedBubbleElem = document.getElementById('openClosedBubble');

    // Check if openClosedBubbleElem doesn't exist, create it
    if (!openClosedBubbleElem) {
        openClosedBubbleElem = document.createElement('div');
        openClosedBubbleElem.id = "openClosedBubble";

        visitGardenImgContainer.appendChild(openClosedBubbleElem);
    }

    let currentDate = new Date();

    // Check if the current time is between the open and close times
    if (currentDate >= timeInfoDict.openDate && currentDate <= timeInfoDict.closeDate) {
        openClosedBubbleElem.className = "rbg-open";
        openClosedBubbleElem.textContent = "THE GARDEN IS OPEN";
    } else {
        openClosedBubbleElem.className = "rbg-closed";
        openClosedBubbleElem.textContent = "THE GARDEN IS CLOSED";
    }

    // Add bootstrap clock icon to openClosedBubbleElem
    let clockIcon = document.createElement('i');
    clockIcon.className = "bi bi-clock float-start";
    openClosedBubbleElem.appendChild(clockIcon);
}


// If concert date; change hours and add buy link
function handleConcertDay(currentMonth, currentDay) {
    // Check if buyLink already exists
    let buyLink = document.getElementById('buyLink');

    if (!buyLink) {
        for (let i = 0; i < concertInfo.length; i++) {
            if (concertInfo[i]["Date"].getMonth() + 1 === currentMonth && concertInfo[i]["Date"].getDate() === currentDay) {
                if (concertInfo[i]["TicketURL"]) {
                    buyLink = document.createElement('a');
                    buyLink.id = "buyLink";
                    buyLink.setAttribute("href", concertInfo[i]["TicketURL"]);
                    buyLink.className = "fw-bold";
                    buyLink.textContent = "Buy tickets to today's show!";
                    hoursElem.after(buyLink);
                }
                hoursElem.textContent = "Today (Concert Day): 9 AM - 5 PM";

                concertDay = true;
                break;
            }
        }
    }
}

setInterval(() => {
    setHours()
}, 60000); // Update every minute

window.onload = () => {
    setHours();
}