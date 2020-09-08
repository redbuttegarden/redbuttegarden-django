window.onload = gardenYearlyHours;

function gardenYearlyHours() {

var d = new Date();
var offset = d.getTimezoneOffset()/60;
var offsetDifference = offset - 6;

var month = d.getMonth() + 1;
var day = d.getDate();


var hours = d.getHours() + offsetDifference;

var minutes = d.getMinutes();


var busHours;
var status;
var hoursInfo;

/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
/* 		Variables to Change Yearly					  										  */
/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
/**/	var daylightEndDay = 4;				// Day that Daylight Savings Time Ends in November of the current year
/**/	var daylightStartDay = 11;			// Day that Daylight Savings Time Begins in March of the next year
/**/
/**/	var thanksgivingDay = 22;			// Day of Month of Thanksgiving Holiday in November
/**/
/**/	var holidayPartyDay = 19;			// Day of Month we close for Holiday Party in December
/**/	var holidayPartyClosingHour = 14; 	// Hour we close on day of Holiday Party (military time)
/**/  var holidayPartyClosingMinute = 0; // Minute we close on day of Holiday Party (military time)
/**/
/**/	var galaMonth = 0;					// Month of Gala
/**/	var galaDay = 0; 					// Day of month of Gala
/**/
/**/	var gadDay1 = 18;					// Day of month in October for 1st day of Garden After Dark
/**/	var gadDay2 = 19;					// Day of month in October for 2nd day of Garden After Dark
/**/	var gadDay3 = 20;					// Day of month in October for 3rd day of Garden After Dark
/**/	var gadDay4 = 25;					// Day of month in October for 4th day of Garden After Dark
/**/	var gadDay5 = 26;					// Day of month in October for 5th day of Garden After Dark
/**/	var gadDay6 = 27;					// Day of month in October for 6th day of Garden After Dark (if applicable; if none, set to zero)
/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/

/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
/* 		Variables For MISC Messages that Appear in Status Divs								  */
/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
/**/	var gardenOpenMessage = "<div style=\x22font-weight:bold;color:#49E20E;\x22>The Garden is Open</div>";
/**/	var gardenClosedMessage = "<div style=\x22color:red;font-weight:bold;\x22>The Garden is Closed Now</div>";
/**/	var gardenWillOpenMessageStart = "<div style=\x22font-weight:bold;color:#FF0000;\x22>The Garden Will Open in ";
/**/	var gardenWillCloseMessageStart = "<div style=\x22font-weight:bold;color:#FF0000;\x22>The Garden Will Close in ";
/**/	var gardenMessageEnd = " Minutes</div>";
/**/	var halfOffAdmission = "Enjoy half-price admission December, January, and February";
/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/

minutesBeforeOpeningorClosing = 60 - minutes;

// Code to account for Daylight Savings Time

if ( (month == 11 && day >= daylightEndDay) || (month == 12) || (month == 1) || (month == 2) || (month == 3 && day < daylightStartDay) ) {

	hours = hours - 1;

}

// Between 8AM and 9AM: shows how many minutes before the garden opens

if (hours == 8 ) {

	status = gardenWillOpenMessageStart+minutesBeforeOpeningorClosing+gardenMessageEnd;
	document.getElementById("gardenStatus").innerHTML = status;

	return;
}

// Takes admission prices, converts them to integers, and divides them by two for half admission in December, January, and February

if ( (month == 12) || (month == 1) || (month == 2) ){

	var adultAdm = document.getElementById("adult-adm").innerHTML;
	var adultHalf = (parseInt(adultAdm, 10))/2;
	document.getElementById("adult-adm").innerHTML = "<span style=\x22text-decoration:line-through;\x22>"+adultAdm+"</span>";
	document.getElementById("adult-half").innerHTML = "&nbsp;&nbsp;$"+adultHalf;


	var seniorAdm = document.getElementById("senior-adm").innerHTML;
	var seniorHalf = (parseInt(seniorAdm, 10))/2;
	document.getElementById("senior-adm").innerHTML = "<span style=\x22text-decoration:line-through;\x22>"+seniorAdm+"</span>";
	document.getElementById("senior-half").innerHTML = "&nbsp;&nbsp;$"+seniorHalf;

	var milAdm = document.getElementById("mil-adm").innerHTML;
	var milHalf = (parseInt(milAdm, 10))/2;
	document.getElementById("mil-adm").innerHTML = "<span style=\x22text-decoration:line-through;\x22>"+milAdm+"</span>";
	document.getElementById("mil-half").innerHTML = "&nbsp;&nbsp;$"+milHalf;

	var childAdm = document.getElementById("child-adm").innerHTML;
	var childHalf = (parseInt(childAdm, 10))/2;
	document.getElementById("child-adm").innerHTML = "<span style=\x22text-decoration:line-through;\x22>"+childAdm+"</span>";
	document.getElementById("child-half").innerHTML = "&nbsp;&nbsp;$"+childHalf;


	var staffAdm = document.getElementById("staff-adm").innerHTML;
	var staffHalf = (parseInt(staffAdm, 10))/2;
	document.getElementById("staff-adm").innerHTML = "<span style=\x22text-decoration:line-through;\x22>"+staffAdm+"</span>";
	document.getElementById("staff-half").innerHTML = "&nbsp;&nbsp;$"+staffHalf;

}

/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
/* CHANGE YEARLY: Early Closing Days for Concerts and Gala  								  */
/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/

	// Hours for individual concert days (which will change every year),
	// the Gala, and other miscellaneous days that we will close at 5PM

	if (
			(month == 5 && day == 31)						// Concert 01 	- Bela Fleck
	|| 	(month == 6 && day == 5) 					  // Concert 02 	- Little Feat
	|| 	(month == 6 && day == 6)						// Concert 03 	- Shakespeare Event
	|| 	(month == 6 && day == 25)						// Concert 04 	- Howard Jones and men without hats
	|| 	(month == 6 && day == 26)						// Concert 05 	- Lucinda Williams
	|| 	(month == 6 && day == 27)						// Concert 06 	- Greensky Bluegrass
	|| 	(month == 7 && day == 2)						// Concert 07 	- Utah Symphony
	|| 	(month == 7 && day == 10) 					// Concert 08 	- Galactic
	|| 	(month == 7 && day == 11)						// Concert 09 	- Pink Martini
	|| 	(month == 7 && day == 14)						// Concert 10 	- Lyle Lovett and his large band
	|| 	(month == 7 && day == 18)						// Concert 11 	- Seal
	|| 	(month == 7 && day == 23)						// Concert 12 	- Nathaniel Rateliff and the nightsweats
	|| 	(month == 7 && day == 26)						// Concert 13 	- Trampled By Turtles
	|| 	(month == 7 && day == 30)						// Concert 14		- John Prine
	|| 	(month == 8 && day == 4)						// Concert 15		- Umphrey's McGee
	|| 	(month == 8 && day == 5)						// Concert 16		- Jonny Lang | JJ Grey and Mofro
	|| 	(month == 8 && day == 7)						// Concert 17		- Mandolin Orange
	|| 	(month == 8 && day == 9)						// Concert 18		- The Mighty O.A.R. w/ American Authors
	|| 	(month == 8 && day == 13)						// Concert 19		- Shakey Graves | Dr. Dog
	|| 	(month == 8 && day == 14)						// Concert 20		- Lord Huron
	|| 	(month == 8 && day == 16)						// Concert 21		- the B-52's
	|| 	(month == 8 && day == 19)						// Concert 22		- Steve Miller Band
	|| 	(month == 8 && day == 26)						// Concert 23		- The Stray Cats
	|| 	(month == 8 && day == 28)						// Concert 24		- The Wood Brothers | Colter Wall
	|| 	(month == 8 && day == 29)						// Concert 25		- Amos Lee
	|| 	(month == 9 && day == 4)						// Concert 26		- Gov't Mule
	|| 	(month == 9 && day == 6)						// Concert 27		- Gary Clark Jr.
	|| 	(month == 9 && day == 11)						// Concert 28		- Mark Knopfler
	|| 	(month == 9 && day == 15)						// Concert 29		- Boz Scaggs
	|| 	(month == 9 && day == 19)						// Concert 30		- Jason Isbell and the 400 Unit
	|| 	(month == 9 && day == 23)						// Concert 31		- Tash Sultana
	|| 	(month == galaMonth && day == galaDay)		// Gala (if applicable)

	)

	{
		busHours = "9AM-5PM";
		document.getElementById("gardenHours").innerHTML = busHours;
		otherNotes = "The Garden Will Close at 5PM for a Concert";

		if (month == galaMonth && day == galaDay) {
			otherNotes = "The Garden Will Close at 5PM for a Special Gala Event";
		}

		document.getElementById("otherNotes").innerHTML = document.getElementById("otherNotes2").innerHTML = otherNotes;

			if (hours >= 9 && hours < 16) {
			status = gardenOpenMessage;
			document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
			return;
		}

			if (hours == 16) {
				status = gardenWillCloseMessageStart+minutesBeforeOpeningorClosing+gardenMessageEnd;
				document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
				return;
		}

			else {
				status = gardenClosedMessage;
				document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
				return;
		}

	return;
	}

// Jan 1 - Mar 31 General Hours

if (month == 1 || month == 2 || month == 3) {

	busHours = "Jan 2-Mar 31: 9AM-5PM";
	document.getElementById("gardenHours").innerHTML = document.getElementById("gardenHours2").innerHTML = busHours;

	if (month == 1 || month == 2) {
		admissionNotes = halfOffAdmission;
		document.getElementById("admissionDiscount").innerHTML =  admissionNotes;
	}


	if (month == 1 && day == 1) {
		status = gardenClosedMessage;
		document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
		otherNotes = "The Garden is Closed Dec 24-Jan 1";
		document.getElementById("otherNotes").innerHTML = document.getElementById("otherNotes2").innerHTML = otherNotes; // Note that we are closed Jan 1st
		return;
	}

		if (hours >= 9 && hours < 16) {
			status = gardenOpenMessage;
			document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
			return;
		}

		if (hours == 16) {
			status = gardenWillCloseMessageStart+minutesBeforeOpeningorClosing+gardenMessageEnd;
			document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
			return;
		}

		else {
			status = gardenClosedMessage;
			document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
			return;
		}

}

// April 1-30 General Hours

else if (month == 4) {

	busHours = "Apr 1-30: 9AM-7:30PM";
	document.getElementById("gardenHours").innerHTML = document.getElementById("gardenHours2").innerHTML = busHours;

		if ((hours >= 9 && hours < 18) || (hours == 18 && minutes < 30)) {
			status = gardenOpenMessage;
			document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
			return;
		}

		if ((hours == 18 && minutes >= 30) || (hours == 19 && minutes < 30)) {

			if (hours == 18 && minutes >= 30) {
				minutesBeforeOpeningorClosing = (60 - minutes) + 30;
			}

			if (hours == 19 && minutes < 30) {
				minutesBeforeOpeningorClosing = 30 - minutes;
			}

			status = gardenWillCloseMessageStart+minutesBeforeOpeningorClosing+gardenMessageEnd;
			document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
			return;
		}

		else {
			status = gardenClosedMessage;
			document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
			return;
		}

}

// May 1 - Aug 31 General Hours

else if (month == 5 || month == 6 || month == 7 || month == 8) {

	busHours = "May 1-Aug 31: 9AM-9PM*";
	otherNotes = "*Garden Hours on Concert Days: 9AM-5PM";
	document.getElementById("gardenHours").innerHTML = document.getElementById("gardenHours2").innerHTML = busHours;
	document.getElementById("otherNotes").innerHTML = document.getElementById("otherNotes2").innerHTML = otherNotes;

		if (hours >= 9 && hours < 20) {
			status = gardenOpenMessage;
			document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
			return;
		}

		if (hours == 20) {
			status = gardenWillCloseMessageStart+minutesBeforeOpeningorClosing+gardenMessageEnd;
			document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
			return;
		}

		else {
			status = gardenClosedMessage;
			document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
			return;
		}

}

// Sep 1 - 30 General Hours

else if (month == 9) {

	busHours = "Sep 1-30: 9AM-7:30PM*";
	otherNotes = "*Garden Hours on Concert Days: 9AM-5PM";

	// Begin Special Event on 9-21-2017 per Development's Request

		 if (month == 9 && day == 21) {
			 otherNotes = "The Garden Will Close at 5PM for a Special Member Event";
		 }
	// End Special EVent

	document.getElementById("gardenHours").innerHTML = document.getElementById("gardenHours2").innerHTML = busHours;
	document.getElementById("otherNotes").innerHTML = document.getElementById("otherNotes2").innerHTML = otherNotes;

		if ((hours >= 9 && hours < 18) || (hours == 18 && minutes < 30)) {
			status = gardenOpenMessage;
			document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
			return;

		}

		if ((hours == 18 && minutes >= 30) || (hours == 19 && minutes < 30)) {

			if (hours == 18 && minutes >= 30) {
				minutesBeforeOpeningorClosing = (60 - minutes) + 30;
			}

			if (hours == 19 && minutes < 30) {
				minutesBeforeOpeningorClosing = 30 - minutes;
			}

			status = gardenWillCloseMessageStart+minutesBeforeOpeningorClosing+gardenMessageEnd;
			document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
			return;
		}

		else {
			status = gardenClosedMessage;
			document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
			return;
		}

}

// Oct 1 - Dec 23 General hours

else if ( month == 10 || month == 11 || month == 12) {

	busHours = "Oct 1-Dec 23: 9AM-5PM";
	otherNotes = "Closed Thanksgiving Day and Dec 24-Jan 1";
	document.getElementById("gardenHours").innerHTML = document.getElementById("gardenHours2").innerHTML = busHours;
	document.getElementById("otherNotes").innerHTML = document.getElementById("otherNotes2").innerHTML = otherNotes;

	if (month == 12) {
		admissionNotes = halfOffAdmission;
		document.getElementById("admissionDiscount").innerHTML =  admissionNotes;
	}

/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
/* Garden After Dark Additional Hours (change gadDay# variables at top yearly)				  */
/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
/**/
/*~~~~~~~Re-enable and edit this code if one of the GAD events has different hours than the rest~~~~~~~*/
//
//		if ( (month == 10) && (day == gadDay5) ) {
//			otherNotes = "<div style=\x22color:#FF9100;font-weight:bold;\x22>The Garden will close at 5PM, then open again from 6-10PM for Garden After Dark</div>";
//			document.getElementById("otherNotes").innerHTML = document.getElementById("otherNotes2").innerHTML = otherNotes;
//			busHours = "9AM-5PM for General Admission<br />6PM-10PM for Garden After Dark";
//			document.getElementById("gardenHours").innerHTML = document.getElementById("gardenHours2").innerHTML = busHours;
//
//			if (hours >= 9 && hours < 16) {
//				status = gardenOpenMessage;
//				document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
//				return;
//			}
//
//			if (hours == 16) {
//				status = "<div style=\x22color:#FF9100;font-weight:bold;\x22>The Garden is Closing Soon, but will reopen at 6PM for Garden After Dark</div>";
//				document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
//				return;
//			}
//
//			if (hours >= 18 && hours < 21) {
//				status = "<div style=\x22color:#FF9100;font-weight:bold;\x22>The Garden is Open for Garden After Dark!</div>";
//				document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
//				return;
//			}
//
//			if (hours == 21) {
//				status = gardenWillCloseMessageStart+minutesBeforeOpeningorClosing+gardenMessageEnd;
//				document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
//				return;
//			}
//
//			else {
//				status = gardenClosedMessage;
//				document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
//				return;
//			}
//
//			return;
//		}
/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
/**/
/**/		if ( (month == 10) && (day == gadDay1 || day == gadDay2 || day == gadDay3 || day == gadDay4 || day == gadDay5 || day == gadDay6) ) {
/**/			otherNotes = "<div style=\x22color:#FF9100;font-weight:bold;\x22>The Garden will close at 5PM, then open again from 6-9PM for Garden After Dark</div>";
/**/			document.getElementById("otherNotes").innerHTML = document.getElementById("otherNotes2").innerHTML = otherNotes;
/**/			busHours = "9AM-5PM for General Admission<br />6PM-9PM for Garden After Dark";
/**/			document.getElementById("gardenHours").innerHTML = document.getElementById("gardenHours2").innerHTML = busHours;
/**/
/**/						if (hours >= 9 && hours < 16) {
/**/				status = gardenOpenMessage;
/**/				document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
/**/				return;
/**/			}
/**/
/**/			if (hours == 16) {
/**/				status = "<div style=\x22color:#FF9100;font-weight:bold;\x22>The Garden is Closing Soon, but will reopen at 6PM for Garden After Dark</div>";
/**/				document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
/**/				return;
/**/			}
/**/
/**/			if (hours >= 18 && hours < 20) {
/**/				status = "<div style=\x22color:#FF9100;font-weight:bold;\x22>The Garden is Open for Garden After Dark!</div>";
/**/				document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
/**/				return;
/**/			}
/**/
/**/			if (hours == 20) {
/**/				status = gardenWillCloseMessageStart+minutesBeforeOpeningorClosing+gardenMessageEnd;
/**/				document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
/**/				return;
/**/			}
/**/
/**/			else {
/**/				status = gardenClosedMessage;
/**/				document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
/**/				return;
/**/			}
/**/
/**/			return;
/**/
/**/		}
/**/
/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/

/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
/* Day Garden is Closed for Thanksgiving (Change thanksgivingDay variable at top yearly)	  */
/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
/**/
/**/	if (month == 11 && day == thanksgivingDay) {
/**/		status = gardenClosedMessage;
/**/		document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
/**/		busHours = "";
/**/		document.getElementById("gardenHours").innerHTML = document.getElementById("gardenHours2").innerHTML = busHours;
/**/		otherNotes = "The Garden is Closed for the Thanksgiving Holiday";
/**/		document.getElementById("otherNotes").innerHTML = document.getElementById("otherNotes2").innerHTML = otherNotes;
/**/		return;
/**/ 	}
/**/
/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/

/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
/* Day/Time Garden Closes for Holiday Party (Change holidayPartyDay variable at top yearly)	  */
/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
/**/	// Shows message that we will close for holiday party on the day before holiday party
/**/	if (month == 12 && day == (holidayPartyDay - 1)) {
/**/		otherNotes = "The Garden Will Close Early Tomorrow at 2PM";
/**/		document.getElementById("otherNotes").innerHTML =  otherNotes;
/**/			return;
/**/		}
/**/
/**/	// Changes business hours to those of holiday party and adds note for public
/**/	if (month == 12 && day == holidayPartyDay) {
/**/		status = gardenClosedMessage;
/**/		document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
/**/		busHours = "9AM-2PM";
/**/		document.getElementById("gardenHours").innerHTML = document.getElementById("gardenHours2").innerHTML = busHours;
/**/		otherNotes = "The Garden Will Close Early for our Annual Staff Holiday Party";
/**/		document.getElementById("otherNotes").innerHTML = document.getElementById("otherNotes2").innerHTML = otherNotes;
/**/
/**/		if ( (hours >= 9) && (hours < holidayPartyClosingHour) ) {
/**/			status = gardenOpenMessage;
/**/			document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
/**/			return;
/**/		}
/**/
/**/		else if ( ( (hours == holidayPartyClosingHour - 1) && (minutes < holidayPartyClosingMinute) ) ) {
/**/			status = gardenWillCloseMessageStart+minutesBeforeOpeningorClosing+gardenMessageEnd;
/**/			document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
/**/			return;
/**/		}
/**/
/**/		else {
/**/			status = gardenClosedMessage;
/**/			document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
/**/			return;
/**/		}
/**/
/**/		return;
/**/	}
/**/
/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/

/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
/* Displays that Garden is Closed from Dec 24th-Jan 1st (Never needs to be changed)			  */
/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
/**/
/**/		if (month == 12 && day >= 24) {
/**/			status = gardenClosedMessage;
/**/			document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
/**/			busHours = "";
/**/			document.getElementById("gardenHours").innerHTML = document.getElementById("gardenHours2").innerHTML = busHours;
/**/			otherNotes = "The Garden is Closed Dec 24-Jan 1";
/**/			document.getElementById("otherNotes").innerHTML = document.getElementById("otherNotes2").innerHTML = otherNotes;
/**/			return;
/**/		}
/**/
/**/		else if (hours >= 9 && hours < 16) {
/**/			status = gardenOpenMessage;
/**/			document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
/**/			return;
/**/		}
/**/
/**/		else if (hours == 16) {
/**/			status = gardenWillCloseMessageStart+minutesBeforeOpeningorClosing+gardenMessageEnd;
/**/			document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
/**/			return;
/**/		}
/**/
/**/		else {
/**/			status = gardenClosedMessage;
/**/			document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
/**/			return;
/**/		}
/**/
/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/

	if (hours >= 9 && hours < 16) {
		status = gardenOpenMessage;
		document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
		return;
	}

	if (hours == 16) {
		status = gardenWillCloseMessageStart+minutesBeforeOpeningorClosing+gardenMessageEnd;
		document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
		return;
	}

	else {
		status = gardenClosedMessage;
		document.getElementById("gardenStatus").innerHTML = document.getElementById("gardenStatus2").innerHTML = status;
		return;
	}


}

return;

}
