window.onload = setHours;

let d = new Date();
let offset = d.getTimezoneOffset()/60;
let offsetDifference = offset - 6;

let month = d.getMonth() + 1;
let day = d.getDate();


let hours = d.getHours() + offsetDifference;

let minutes = d.getMinutes();


let busHours;
let status;

const manualOverrideTrue = (document.getElementById('hours_override').textContent === 'True')

// TODO - Create functions that automatically determine these dates

const daylightEndDay = 1;  // Day that Daylight Savings Time Ends in November of the current year
const daylightStartDay = 8;  // Day that Daylight Savings Time Begins in March of the next year

const thanksgivingDay = 26;  // Day of Month of Thanksgiving Holiday in November

const holidayPartyDay = parseInt(document.getElementById('hours_holiday_day').textContent);  // Day of Month we close for Holiday Party in December
const holidayPartyClosingHour = parseInt(document.getElementById('hours_holiday_hour').textContent);  // Hour we close on day of Holiday Party (military time)
const holidayPartyClosingMinute = parseInt(document.getElementById('hours_holiday_minute').textContent);  // Minute we close on day of Holiday Party (military time)

const galaMonth = 0;  // Month of Gala
const galaDay = 0;  // Day of month of Gala

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

let minutesBeforeOpeningOrClosing = 60 - minutes;

function setHours() {
	if (manualOverrideTrue) {
		const openHour = document.getElementById("hours_man_open").textContent;
		const closeHour = document.getElementById("hours_man_close").textContent;
		busHours = openHour + " &ndash; " + closeHour;
		// Check if hours_man_open and hours_man_close is actually set before setting the gardenHours content, otherwise we end up with just the '-'
		if (openHour && closeHour) {
			document.getElementById("gardenHours").innerHTML = busHours;
		}
		document.getElementById("gardenStatus").innerHTML = document.getElementById("hours_man_add_msg").textContent;
		document.getElementById("gardenEmphatic").innerHTML = document.getElementById("hours_man_add_emph_msg").textContent;
	} else {
		gardenYearlyHours();
	}
}

function gardenYearlyHours() {

	// Code to account for Daylight Savings Time

	if ( (month === 11 && day >= daylightEndDay) || (month === 12) || (month === 1) || (month === 2) || (month === 3 && day < daylightStartDay) ) {

		hours = hours - 1;
	}

	// Between 8AM and 9AM: shows how many minutes before the garden opens

	if (hours === 8 ) {

		status = gardenWillOpenMessageStart + minutesBeforeOpeningOrClosing + gardenMessageEnd;
		document.getElementById("gardenStatus").innerHTML = status;

		return;
	}

	// Takes admission prices, converts them to integers, and divides them by two for half admission in December, January, and February

	if ( (month === 12) || (month === 1) || (month === 2) ){

		const adultAdm = document.getElementById("adult-adm").innerHTML;
		const adultHalf = (parseInt(adultAdm, 10))/2;
		document.getElementById("adult-adm").innerHTML = "<span style=\x22text-decoration:line-through;\x22>"+adultAdm+"</span>";
		document.getElementById("adult-half").innerHTML = "&nbsp;&nbsp;$"+adultHalf;


		const seniorAdm = document.getElementById("senior-adm").innerHTML;
		const seniorHalf = (parseInt(seniorAdm, 10))/2;
		document.getElementById("senior-adm").innerHTML = "<span style=\x22text-decoration:line-through;\x22>"+seniorAdm+"</span>";
		document.getElementById("senior-half").innerHTML = "&nbsp;&nbsp;$"+seniorHalf;

		const milAdm = document.getElementById("mil-adm").innerHTML;
		const milHalf = (parseInt(milAdm, 10))/2;
		document.getElementById("mil-adm").innerHTML = "<span style=\x22text-decoration:line-through;\x22>"+milAdm+"</span>";
		document.getElementById("mil-half").innerHTML = "&nbsp;&nbsp;$"+milHalf;

		const childAdm = document.getElementById("child-adm").innerHTML;
		const childHalf = (parseInt(childAdm, 10))/2;
		document.getElementById("child-adm").innerHTML = "<span style=\x22text-decoration:line-through;\x22>"+childAdm+"</span>";
		document.getElementById("child-half").innerHTML = "&nbsp;&nbsp;$"+childHalf;


		const staffAdm = document.getElementById("staff-adm").innerHTML;
		const staffHalf = (parseInt(staffAdm, 10))/2;
		document.getElementById("staff-adm").innerHTML = "<span style=\x22text-decoration:line-through;\x22>"+staffAdm+"</span>";
		document.getElementById("staff-half").innerHTML = "&nbsp;&nbsp;$"+staffHalf;

	}

	// TODO - Pass Concert objects to view so hours.js knows about early closing times
	/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
	/* CHANGE YEARLY: Early Closing Days for Concerts and Gala  								  */
	/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/

	// Hours for individual concert days (which will change every year),
	// the Gala, and other miscellaneous days that we will close at 5PM

	if (month === galaMonth && day === galaDay)		// Gala (if applicable)

	{
		busHours = "9AM-5PM";
		document.getElementById("gardenHours").innerHTML = busHours;
		otherNotes = "The Garden Will Close at 5PM for a Concert";

		if (month === galaMonth && day === galaDay) {
			otherNotes = "The Garden Will Close at 5PM for a Special Gala Event";
		}

		document.getElementById("otherNotes").innerHTML = otherNotes;

		if (hours >= 9 && hours < 16) {
			status = gardenOpenMessage;
			document.getElementById("gardenStatus").innerHTML = status;
			return;
		}

		if (hours === 16) {
			status = gardenWillCloseMessageStart+minutesBeforeOpeningOrClosing+gardenMessageEnd;
			document.getElementById("gardenStatus").innerHTML = status;
			return;
		}

		else {
			status = gardenClosedMessage;
			document.getElementById("gardenStatus").innerHTML = status;
			return;
		}
	}

	// Jan 1 - Mar 31 General Hours

	if (month === 1 || month === 2 || month === 3) {

		busHours = "Jan 2-Mar 31: 9AM-5PM";
		document.getElementById("gardenHours").innerHTML = busHours;

		if (month === 1 || month === 2) {
			admissionNotes = halfOffAdmission;
			document.getElementById("admissionDiscount").innerHTML =  admissionNotes;
		}


		if (month === 1 && day === 1) {
			status = gardenClosedMessage;
			document.getElementById("gardenStatus").innerHTML = status;
			otherNotes = "The Garden is Closed Dec 24-Jan 1";
			document.getElementById("otherNotes").innerHTML = otherNotes; // Note that we are closed Jan 1st
			return;
		}

		if (hours >= 9 && hours < 16) {
			status = gardenOpenMessage;
			document.getElementById("gardenStatus").innerHTML = status;
			return;
		}

		if (hours === 16) {
			status = gardenWillCloseMessageStart+minutesBeforeOpeningOrClosing+gardenMessageEnd;
			document.getElementById("gardenStatus").innerHTML = status;
		}

		else {
			status = gardenClosedMessage;
			document.getElementById("gardenStatus").innerHTML = status;
		}
	}

// April 1-30 General Hours

	else if (month === 4) {

		busHours = "Apr 1-30: 9AM-7:30PM";
		document.getElementById("gardenHours").innerHTML = busHours;

		if ((hours >= 9 && hours < 18) || (hours === 18 && minutes < 30)) {
			status = gardenOpenMessage;
			document.getElementById("gardenStatus").innerHTML = status;
			return;
		}

		if ((hours === 18 && minutes >= 30) || (hours === 19 && minutes < 30)) {

			if (hours === 18 && minutes >= 30) {
				minutesBeforeOpeningOrClosing = (60 - minutes) + 30;
			}

			if (hours === 19 && minutes < 30) {
				minutesBeforeOpeningOrClosing = 30 - minutes;
			}

			status = gardenWillCloseMessageStart+minutesBeforeOpeningOrClosing+gardenMessageEnd;
			document.getElementById("gardenStatus").innerHTML = status;
		}

		else {
			status = gardenClosedMessage;
			document.getElementById("gardenStatus").innerHTML = status;
		}
	}

// May 1 - Aug 31 General Hours

	else if (month === 5 || month === 6 || month === 7 || month === 8) {

		busHours = "May 1-Aug 31: 9AM-9PM*";
		otherNotes = "*Garden Hours on Concert Days: 9AM-5PM";
		document.getElementById("gardenHours").innerHTML = busHours;
		document.getElementById("otherNotes").innerHTML = otherNotes;

		if (hours >= 9 && hours < 20) {
			status = gardenOpenMessage;
			document.getElementById("gardenStatus").innerHTML = status;
			return;
		}

		if (hours === 20) {
			status = gardenWillCloseMessageStart+minutesBeforeOpeningOrClosing+gardenMessageEnd;
			document.getElementById("gardenStatus").innerHTML = status;
		}

		else {
			status = gardenClosedMessage;
			document.getElementById("gardenStatus").innerHTML = status;
		}
	}

// Sep 1 - 30 General Hours

	else if (month === 9) {

		busHours = "Sep 1-30: 9AM-7:30PM*";
		otherNotes = "*Garden Hours on Concert Days: 9AM-5PM";

		document.getElementById("gardenHours").innerHTML = busHours;
		document.getElementById("otherNotes").innerHTML = otherNotes;

		if ((hours >= 9 && hours < 18) || (hours === 18 && minutes < 30)) {
			status = gardenOpenMessage;
			document.getElementById("gardenStatus").innerHTML = status;
			return;

		}

		if ((hours === 18 && minutes >= 30) || (hours === 19 && minutes < 30)) {

			if (hours === 18 && minutes >= 30) {
				minutesBeforeOpeningOrClosing = (60 - minutes) + 30;
			}

			if (hours === 19 && minutes < 30) {
				minutesBeforeOpeningOrClosing = 30 - minutes;
			}

			status = gardenWillCloseMessageStart+minutesBeforeOpeningOrClosing+gardenMessageEnd;
			document.getElementById("gardenStatus").innerHTML = status;
		}

		else {
			status = gardenClosedMessage;
			document.getElementById("gardenStatus").innerHTML = status;
		}
	}

// Oct 1 - Dec 23 General hours

	else if ( month === 10 || month === 11 || month === 12) {

		busHours = "Oct 1-Dec 23: 9AM-5PM";
		otherNotes = "Closed Thanksgiving Day and Dec 24-Jan 1";
		document.getElementById("gardenHours").innerHTML = busHours;
		document.getElementById("otherNotes").innerHTML = otherNotes;

		if (month === 12) {
			admissionNotes = halfOffAdmission;
			document.getElementById("admissionDiscount").innerHTML =  admissionNotes;
		}


		if ( (month === 10) && (day === gadDay1 || day === gadDay2 || day === gadDay3 || day === gadDay4 || day === gadDay5 || day === gadDay6) ) {
			otherNotes = "<div style=\x22color:#FF9100;font-weight:bold;\x22>The Garden will close at 5PM, then open again from 6-9PM for Garden After Dark</div>";
			document.getElementById("otherNotes").innerHTML = otherNotes;
			busHours = "9AM-5PM for General Admission<br />6PM-9PM for Garden After Dark";
			document.getElementById("gardenHours").innerHTML = busHours;

			if (hours >= 9 && hours < 16) {
				status = gardenOpenMessage;
				document.getElementById("gardenStatus").innerHTML = status;
				return;
			}

			if (hours === 16) {
				status = "<div style=\x22color:#FF9100;font-weight:bold;\x22>The Garden is Closing Soon, but will reopen at 6PM for Garden After Dark</div>";
				document.getElementById("gardenStatus").innerHTML = status;
				return;
			}

			if (hours >= 18 && hours < 20) {
				status = "<div style=\x22color:#FF9100;font-weight:bold;\x22>The Garden is Open for Garden After Dark!</div>";
				document.getElementById("gardenStatus").innerHTML = status;
				return;
			}

			if (hours === 20) {
				status = gardenWillCloseMessageStart+minutesBeforeOpeningOrClosing+gardenMessageEnd;
				document.getElementById("gardenStatus").innerHTML = status;
				return;
			}

			else {
				status = gardenClosedMessage;
				document.getElementById("gardenStatus").innerHTML = status;
				return;
			}
		}


		if (month === 11 && day === thanksgivingDay) {
			status = gardenClosedMessage;
			document.getElementById("gardenStatus").innerHTML = status;
			busHours = "";
			document.getElementById("gardenHours").innerHTML = busHours;
			otherNotes = "The Garden is Closed for the Thanksgiving Holiday";
			document.getElementById("otherNotes").innerHTML = otherNotes;
			return;
		}



		// Shows message that we will close for holiday party on the day before holiday party
		if (month === 12 && day === (holidayPartyDay - 1)) {
			otherNotes = "The Garden Will Close Early Tomorrow at 2PM";
			document.getElementById("otherNotes").innerHTML =  otherNotes;
			return;
		}

		// Changes business hours to those of holiday party and adds note for public
		if (month === 12 && day === holidayPartyDay) {
			status = gardenClosedMessage;
			document.getElementById("gardenStatus").innerHTML = status;
			busHours = "9AM-2PM";
			document.getElementById("gardenHours").innerHTML = busHours;
			otherNotes = "The Garden Will Close Early for our Annual Staff Holiday Party";
			document.getElementById("otherNotes").innerHTML = otherNotes;

			if ( (hours >= 9) && (hours < holidayPartyClosingHour) ) {
				status = gardenOpenMessage;
				document.getElementById("gardenStatus").innerHTML = status;
				return;
			}

			else if ( ( (hours === holidayPartyClosingHour - 1) && (minutes < holidayPartyClosingMinute) ) ) {
				status = gardenWillCloseMessageStart+minutesBeforeOpeningOrClosing+gardenMessageEnd;
				document.getElementById("gardenStatus").innerHTML = status;
				return;
			}

			else {
				status = gardenClosedMessage;
				document.getElementById("gardenStatus").innerHTML = status;
				return;
			}

		}

		if (month === 12 && day >= 24) {
			status = gardenClosedMessage;
			document.getElementById("gardenStatus").innerHTML = status;
			busHours = "";
			document.getElementById("gardenHours").innerHTML = busHours;
			otherNotes = "The Garden is Closed Dec 24-Jan 1";
			document.getElementById("otherNotes").innerHTML = otherNotes;
		}

		else if (hours >= 9 && hours < 16) {
			status = gardenOpenMessage;
			document.getElementById("gardenStatus").innerHTML = status;
		}

		else if (hours === 16) {
			status = gardenWillCloseMessageStart+minutesBeforeOpeningOrClosing+gardenMessageEnd;
			document.getElementById("gardenStatus").innerHTML = status;
		}

		else {
			status = gardenClosedMessage;
			document.getElementById("gardenStatus").innerHTML = status;
		}
	}
}
