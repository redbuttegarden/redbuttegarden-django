window.onload = setHours;

const desktopHours = document.getElementById("gardenHours");
const mobileHours = document.getElementById("gardenHours2");

let busHours;
let status;
let otherNotes = "";
let buyLink;

// Bootanical Dates
bootanicalDates = [];

// Keep this Bootanical list up-to-date each year
bootanicalDates.push(new Date(2023, 10, 18))
bootanicalDates.push(new Date(2023, 10, 19))
bootanicalDates.push(new Date(2023, 10, 20))
bootanicalDates.push(new Date(2023, 10, 21))
bootanicalDates.push(new Date(2023, 10, 22))
bootanicalDates.push(new Date(2023, 10, 23))
bootanicalDates.push(new Date(2023, 10, 24))
bootanicalDates.push(new Date(2023, 10, 25))
bootanicalDates.push(new Date(2023, 10, 26))
// The 27th is a special case to be handled separately
bootanicalDates.push(new Date(2023, 10, 28))
bootanicalDates.push(new Date(2023, 10, 29))
bootanicalDates.push(new Date(2023, 10, 30))

//#region Constant Garden status variables and messages
const manualOverrideTrue = (document.getElementById('hours_override').textContent === 'True')

const daylightEndDay = 3;  // Day that Daylight Savings Time Ends in November of the current year
const daylightStartDay = 9;  // Day that Daylight Savings Time Begins in March of the next year

const thanksgivingDay = 28;  // Day of Month of Thanksgiving Holiday in November

const holidayPartyDay = parseInt(document.getElementById('hours_holiday_day').textContent);  // Day of Month we close for Holiday Party in December
const holidayPartyClosingHour = parseInt(document.getElementById('hours_holiday_hour').textContent);  // Hour we close on day of Holiday Party (military time)
const holidayPartyClosingMinute = parseInt(document.getElementById('hours_holiday_minute').textContent);  // Minute we close on day of Holiday Party (military time)


/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
/* 		For MISC Messages that Appear in Status Divs								  */
/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
const gardenOpenMessage = "<div style=\x22font-weight:bold;color:#49E20E;\x22>The Garden is Open</div>";
const gardenClosedMessage = "<div style=\x22color:red;font-weight:bold;\x22>The Garden is Closed Now</div>";
const gardenWillOpenMessageStart = "<div style=\x22font-weight:bold;color:#FF0000;\x22>The Garden Will Open in ";
const gardenWillCloseMessageStart = "<div style=\x22font-weight:bold;color:#FF0000;\x22>The Garden Will Close in ";
const gardenMessageEnd = " Minutes</div>";
const halfOffAdmission = "Enjoy half-price admission December, January, and February";
/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/

//#endregion


function setHours() {

    let d = new Date();
    let offset = d.getTimezoneOffset() / 60;
    let offsetDifference = offset - 6;

    let currentMonth = d.getMonth() + 1;
    let currentDay = d.getDate();
    let currentHour = d.getHours() + offsetDifference;
    let currentMinute = d.getMinutes();
    let minutesBeforeOpeningOrClosing = 60 - currentMinute;

    if (manualOverrideTrue) {
        const openHour = document.getElementById("hours_man_open").textContent;
        const closeHour = document.getElementById("hours_man_close").textContent;
        busHours = openHour + " &ndash; " + closeHour;
        // Check if hours_man_open and hours_man_close is actually set before setting the gardenHours content, otherwise we end up with just the '-'
        if (openHour && closeHour) {
            // Large Screens
            document.getElementById("gardenHours").textContent = busHours;
            // Mobile
            document.getElementById("gardenHours2").textContent = busHours;
        }
        document.getElementById("gardenStatus").textContent = document.getElementById("hours_man_add_msg").textContent;
        document.getElementById("gardenStatus2").textContent = document.getElementById("hours_man_add_msg").textContent;
        document.getElementById("gardenEmphatic").textContent = document.getElementById("hours_man_add_emph_msg").textContent;
    } else {
        gardenYearlyHours(currentMonth, currentDay, currentHour, currentMinute, minutesBeforeOpeningOrClosing);
    }
}


// Return true if today is a concert day
function handleConcertDay(currentMonth, currentDay, currentHour, minutesBeforeOpeningOrClosing) {
    for (let i = 0; i < concertInfo.length; i++) {
        if (concertInfo[i]["Date"].getMonth() + 1 === currentMonth && concertInfo[i]["Date"].getDate() === currentDay) {
            if (concertInfo[i]["TicketURL"]) {
                buyLink = document.createElement('a');
                buyLink.setAttribute("href", concertInfo[i]["TicketURL"]);
                buyLink.style.cssText = "margin-left:0.2em;";
                buyLink.textContent = "Buy now!";
            }

            busHours = "Today (Concert Day): 9am-5pm";

            if (currentHour >= 9 && currentHour < 16) {
                status = gardenOpenMessage;
            }

            if (currentHour === 16) {
                status = gardenWillCloseMessageStart + minutesBeforeOpeningOrClosing + gardenMessageEnd;
            } else if (currentHour >= 17) {
                status = gardenClosedMessage;
            }

            return true;
        }
    }

    return false;
}


function handleBootanicalDay(currentMonth, currentDay, currentHour, minutesBeforeOpeningOrClosing) {
    for (let i = 0; i < bootanicalDates.length; i++) {
        if (bootanicalDates[i].getMonth() === currentMonth && bootanicalDates[i].getDate() === currentDay) {
            busHours = "9AM-5PM for BOOtanical Days<br />6PM-9PM for BOOtanical Nights";
            otherNotes = "<div style=\x22color:#FF9100;font-weight:bold;\x22>The Garden will close at 5PM, then open again from 6-9PM for BOOtanical Nights</div>";

            if (currentHour >= 9 && currentHour < 16) {
                status = gardenOpenMessage;
            }

            if (currentHour === 16) {
                status = gardenWillCloseMessageStart + minutesBeforeOpeningOrClosing + gardenMessageEnd;
            } else if (currentHour >= 17) {
                status = gardenClosedMessage;
            }

            break;
        }
    }
}


function gardenYearlyHours(currentMonth, currentDay, currentHour, currentMinute, minutesBeforeOpeningOrClosing) {
    // Code to account for Daylight Savings Time
    if ((currentMonth === 11 && currentDay >= daylightEndDay) || (currentMonth === 12) || (currentMonth === 1) || (currentMonth === 2) || (currentMonth === 3 && currentDay < daylightStartDay)) {
        currentHour = currentHour - 1;
    }

    // Takes admission prices, converts them to integers, and divides them by two for half admission in December, January, and February
    if ((currentMonth === 12) || (currentMonth === 1) || (currentMonth === 2)) {

        let adultAdm = document.getElementById("adult-adm").innerHTML;
        adultAdm = adultAdm.replace(/\D/g, "");
        const adultHalf = (parseInt(adultAdm, 10)) / 2;
        document.getElementById("adult-adm").innerHTML = "<span style=\x22text-decoration:line-through;\x22>" + adultAdm + "</span>";
        document.getElementById("adult-half").innerHTML = "&nbsp;&nbsp;$" + adultHalf;


        let seniorAdm = document.getElementById("senior-adm").innerHTML;
        seniorAdm = seniorAdm.replace(/\D/g, "");
        const seniorHalf = (parseInt(seniorAdm, 10)) / 2;
        document.getElementById("senior-adm").innerHTML = "<span style=\x22text-decoration:line-through;\x22>" + seniorAdm + "</span>";
        document.getElementById("senior-half").innerHTML = "&nbsp;&nbsp;$" + seniorHalf;

        let milAdm = document.getElementById("mil-adm").innerHTML;
        milAdm = milAdm.replace(/\D/g, "");
        const milHalf = (parseInt(milAdm, 10)) / 2;
        document.getElementById("mil-adm").innerHTML = "<span style=\x22text-decoration:line-through;\x22>" + milAdm + "</span>";
        document.getElementById("mil-half").innerHTML = "&nbsp;&nbsp;$" + milHalf;

        let childAdm = document.getElementById("child-adm").innerHTML;
        childAdm = childAdm.replace(/\D/g, "");
        const childHalf = (parseInt(childAdm, 10)) / 2;
        document.getElementById("child-adm").innerHTML = "<span style=\x22text-decoration:line-through;\x22>" + childAdm + "</span>";
        document.getElementById("child-half").innerHTML = "&nbsp;&nbsp;$" + childHalf;
    }

    // Jan 1 - Feb 28 General Hours

    if (currentMonth === 1 || currentMonth === 2) {

        // Between 9AM and 10AM: shows how many minutes before the garden opens
        if (currentHour === 9) {
            status = gardenWillOpenMessageStart + minutesBeforeOpeningOrClosing + gardenMessageEnd;
        }

        busHours = "Jan 2 - Feb 28: 10AM-5PM";

        document.getElementById("admissionDiscount").innerHTML = halfOffAdmission;

        if (currentMonth === 1 && currentDay === 1) {
            status = gardenClosedMessage;
            otherNotes = "The Garden is Closed Dec 24-Jan 1";
        } else if (currentHour >= 10 && currentHour < 16) {
            status = gardenOpenMessage;
        } else if (currentHour === 16) {
            status = gardenWillCloseMessageStart + minutesBeforeOpeningOrClosing + gardenMessageEnd;
        } else {
            status = gardenClosedMessage;
        }
    }

    // March General Hours

    if (currentMonth === 3) {

        // Between 8AM and 9AM: shows how many minutes before the garden opens
        if (currentHour === 8) {
            status = gardenWillOpenMessageStart + minutesBeforeOpeningOrClosing + gardenMessageEnd;
        }

        busHours = "March hours: 9AM-5PM";

        if (currentMonth === 1 || currentMonth === 2) {
            document.getElementById("admissionDiscount").innerHTML = halfOffAdmission;
        }

        if (currentMonth === 1 && currentDay === 1) {
            status = gardenClosedMessage;
            otherNotes = "The Garden is Closed Dec 24-Jan 1";
        } else if (currentHour >= 9 && currentHour < 16) {
            status = gardenOpenMessage;
        } else if (currentHour === 16) {
            status = gardenWillCloseMessageStart + minutesBeforeOpeningOrClosing + gardenMessageEnd;
        } else {
            status = gardenClosedMessage;
        }
    }

    // April 1-30 General Hours
    else if (currentMonth === 4) {

        // Between 8AM and 9AM: shows how many minutes before the garden opens
        if (currentHour === 8) {
            status = gardenWillOpenMessageStart + minutesBeforeOpeningOrClosing + gardenMessageEnd;
        }

        busHours = "April hours: 9AM-7:30PM";

        if ((currentHour >= 9 && currentHour < 18) || (currentHour === 19 && currentMinute < 30)) {
            status = gardenOpenMessage;
        } else if ((currentHour === 18 && currentMinute >= 30) || (currentHour === 19 && currentMinute < 30)) {

            if (currentHour === 18 && currentMinute >= 30) {
                minutesBeforeOpeningOrClosing = (60 - currentMinute) + 30;
            }

            if (currentHour === 19 && currentMinute < 30) {
                minutesBeforeOpeningOrClosing = 30 - currentMinute;
            }

            status = gardenWillCloseMessageStart + minutesBeforeOpeningOrClosing + gardenMessageEnd;
        } else {
            status = gardenClosedMessage;
        }
    }

    // May 1 - Aug 31 General Hours
    else if (currentMonth === 5 || currentMonth === 6 || currentMonth === 7 || currentMonth === 8) {

        // Between 8AM and 9AM: shows how many minutes before the garden opens
        if (currentHour === 8) {
            status = gardenWillOpenMessageStart + minutesBeforeOpeningOrClosing + gardenMessageEnd;
        }

        busHours = "May 1-Aug 31: 9AM-9PM*";
        otherNotes = "*Garden Hours on Concert Days: 9AM-5PM";

        // handleConcertDate will set appropriate business hours and status message if today is a concert date and true if it is
        if (!handleConcertDay(currentMonth, currentDay, currentHour, minutesBeforeOpeningOrClosing)) {
            // If it's not a concert day we set the status here
            if (currentHour >= 9 && currentHour < 20) {
                status = gardenOpenMessage;
            } else if (currentHour === 20) {
                status = gardenWillCloseMessageStart + minutesBeforeOpeningOrClosing + gardenMessageEnd;
            } else {
                status = gardenClosedMessage;
            }
        }
    }

    // Sep 1 - 30 General Hours
    else if (currentMonth === 9) {

        // Between 8AM and 9AM: shows how many minutes before the garden opens
        if (currentHour === 8) {
            status = gardenWillOpenMessageStart + minutesBeforeOpeningOrClosing + gardenMessageEnd;
        }

        busHours = "Sep 1-30: 9AM-7:30PM*";

        // Specific check for Teton Gravity Event on Sept. 20th; Will be removed on Sept. 21st
        if (currentDay === 20)
            otherNotes = "*Garden Hours on Event Days: 9AM-5PM";
        else
            otherNotes = "*Garden Hours on Concert Days: 9AM-5PM";

        // handleConcertDate will set appropriate business hours and status message if today is a concert date and true if it is
        if (!handleConcertDay(currentMonth, currentDay, currentHour, minutesBeforeOpeningOrClosing)) {
            // If it's not a concert day we set the status here
            if ((currentHour >= 9 && currentHour < 18) || (currentHour === 18 && currentMinute < 30)) {
                status = gardenOpenMessage;
            } else if (currentHour === 18 && currentMinute >= 30) {
                minutesBeforeOpeningOrClosing = (60 - currentMinute) + 30;
                status = gardenWillCloseMessageStart + minutesBeforeOpeningOrClosing + gardenMessageEnd;
            } else if (currentHour === 19 && currentMinute < 30) {
                minutesBeforeOpeningOrClosing = 30 - currentMinute;
                status = gardenWillCloseMessageStart + minutesBeforeOpeningOrClosing + gardenMessageEnd;
            } else {
                status = gardenClosedMessage;
            }
        }
    }

    // Oct 1 - Dec 23 General hours
    else if (currentMonth === 10 || currentMonth === 11 || currentMonth === 12) {

        // Between 8AM and 9AM: shows how many minutes before the garden opens
        if (currentHour === 8) {
            status = gardenWillOpenMessageStart + minutesBeforeOpeningOrClosing + gardenMessageEnd;
        }

        busHours = "Oct 1-Dec 23: 9AM-5PM";
        otherNotes = "Closed Thanksgiving Day and Dec 24-Jan 1";

        if (currentMonth === 10) {
            handleBootanicalDay(currentMonth, currentDay, currentHour, minutesBeforeOpeningOrClosing);
        } else if (currentMonth === 11 && currentDay === thanksgivingDay) {
            status = gardenClosedMessage;
            busHours = "";
            otherNotes = "The Garden is Closed for the Thanksgiving Holiday";
        } else if (currentMonth === 12) {
            document.getElementById("admissionDiscount").innerHTML = halfOffAdmission;
        }

        if (currentMonth === 12 && currentDay === (holidayPartyDay - 1)) {
            otherNotes = "The Garden Will Close Early Tomorrow at 2PM";
        } else if (currentMonth === 12 && currentDay === holidayPartyDay) {
            status = gardenClosedMessage;
            busHours = "9AM-2PM";
            otherNotes = "The Garden Will Close Early for our Annual Staff Holiday Party";

            if ((currentHour >= 9) && (currentHour < holidayPartyClosingHour)) {
                status = gardenOpenMessage;
            } else if (((currentHour === holidayPartyClosingHour - 1) && (currentMinute < holidayPartyClosingMinute))) {
                status = gardenWillCloseMessageStart + minutesBeforeOpeningOrClosing + gardenMessageEnd;
            } else {
                status = gardenClosedMessage;
            }
        } else if (currentMonth === 12 && currentDay >= 24) {
            status = gardenClosedMessage;
            busHours = "";
            otherNotes = "The Garden is Closed Dec 24-Jan 1";
        } else if (currentHour >= 9 && currentHour < 16) {
            status = gardenOpenMessage;
        } else if (currentHour === 16) {
            status = gardenWillCloseMessageStart + minutesBeforeOpeningOrClosing + gardenMessageEnd;
        } else {
            status = gardenClosedMessage;
        }
    }

    writeDataToPage();
}

function writeDataToPage() {
    desktopHours.textContent = busHours;
    mobileHours.textContent = busHours;

    if (buyLink) {
        desktopHours.appendChild(buyLink.cloneNode(true));
        mobileHours.appendChild(buyLink.cloneNode(true));
    }

    document.getElementById("gardenStatus").innerHTML = status;
    document.getElementById("otherNotes").innerHTML = otherNotes;
}

setInterval(setHours, 60000); // Update every minute
