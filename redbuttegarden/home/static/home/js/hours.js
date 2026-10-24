/** Display the first matching schedule using the garden's local calendar. */
const pageID = document.getElementById('pageID')?.textContent;
const hoursElem = document.getElementById('hours');
const visitTextElem = document.getElementById('visitText');
const emphaticTextElem = document.getElementById('emphaticText');
const concertInfo = JSON.parse(document.getElementById('concert-info')?.textContent || '[]');

async function getGardenHours() {
    if (!pageID) return null;
    try {
        const response = await fetch(`/api/hours/${pageID}`, {
            headers: {'X-Requested-With': 'XMLHttpRequest'},
        });
        if (!response.ok || response.status === 204) return null;
        return await response.json();
    } catch {
        return null;
    }
}

/** Get Denver calendar parts independently of the visitor's timezone and DST. */
function gardenDateParts(date) {
    const parts = new Intl.DateTimeFormat('en-US', {
        timeZone: 'America/Denver', year: 'numeric', month: '2-digit', day: '2-digit',
        weekday: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23',
    }).formatToParts(date);
    const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
    return {
        calendarDate: `${values.year}-${values.month}-${values.day}`,
        month: Number(values.month) - 1,
        weekday: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].indexOf(values.weekday),
        minutes: Number(values.hour) * 60 + Number(values.minute) + Number(values.second) / 60,
    };
}

function getFirstRBGHoursMatch(rbgHours, currentMonth, dayIndex) {
    return Object.values(rbgHours || {}).find((hours) =>
        Array.isArray(hours?.months_of_year) && hours.months_of_year.includes(currentMonth) &&
        Array.isArray(hours.days_of_week) && hours.days_of_week.includes(dayIndex)
    ) || null;
}

function timeMinutes(value) {
    if (typeof value !== 'string' || !/^\d{1,2}:\d{2}$/.test(value)) return null;
    const [hour, minute] = value.split(':').map(Number);
    return hour < 24 && minute < 60 ? hour * 60 + minute : null;
}

function formatTime(minutes) {
    const hour = Math.floor(minutes / 60);
    const minute = minutes % 60;
    return `${hour % 12 || 12}${minute ? `:${String(minute).padStart(2, '0')}` : ''} ${hour >= 12 ? 'PM' : 'AM'}`;
}

/** Accept legacy responses while ignoring incomplete periods defensively. */
function scheduleRanges(schedule) {
    const ranges = Array.isArray(schedule.time_ranges) ? schedule.time_ranges : [schedule];
    return ranges.map((range) => ({
        start: timeMinutes(range?.garden_open), end: timeMinutes(range?.garden_close),
        label: typeof range?.label === 'string' ? range.label : '',
    })).filter((range) => range.start !== null && range.end !== null && range.start < range.end)
        .sort((first, second) => first.start - second.start);
}

function displayOpenClosed(isOpen, schedule) {
    const container = document.getElementById('visitInfoImg');
    if (!container) return;
    let bubble = document.getElementById('openClosedBubble');
    if (!bubble) {
        bubble = document.createElement('div');
        bubble.id = 'openClosedBubble';
        bubble.setAttribute('role', 'status');
        container.appendChild(bubble);
    }
    bubble.className = isOpen ? 'rbg-open' : 'rbg-closed';
    bubble.textContent = (isOpen ? schedule.open_message : schedule.closed_message) ||
        (isOpen ? 'THE GARDEN IS OPEN' : 'THE GARDEN IS CLOSED');
    const icon = document.createElement('i');
    icon.className = 'bi bi-clock float-start';
    icon.setAttribute('aria-hidden', 'true');
    bubble.appendChild(icon);
}

function updateConcertLink(concert) {
    document.getElementById('buyLink')?.remove();
    if (!concert?.TicketURL || !hoursElem) return;
    let url;
    try {
        url = new URL(concert.TicketURL, window.location.origin);
    } catch {
        return;
    }
    if (!['http:', 'https:'].includes(url.protocol)) return;
    const link = document.createElement('a');
    link.id = 'buyLink';
    link.href = url.href;
    link.className = 'fw-bold';
    link.textContent = concert.BandName ? `Buy tickets to see ${concert.BandName}!` : "Buy tickets to today's show!";
    hoursElem.after(link);
}

function setHours(rbgHours, date = new Date()) {
    if (!hoursElem) return;
    const today = gardenDateParts(date);
    const schedule = getFirstRBGHoursMatch(rbgHours, today.month, today.weekday);
    hoursElem.replaceChildren();
    if (!schedule) {
        hoursElem.textContent = 'Hours unavailable';
        if (visitTextElem) visitTextElem.replaceChildren();
        if (emphaticTextElem) emphaticTextElem.replaceChildren();
        document.getElementById('openClosedBubble')?.remove();
        updateConcertLink(null);
        return;
    }
    let ranges = scheduleRanges(schedule);
    const concert = concertInfo.find((item) => String(item.Date).slice(0, 10) === today.calendarDate);
    updateConcertLink(concert);
    const concertOverride = concert && ranges.length === 1;
    if (concertOverride) ranges = [{start: 9 * 60, end: 17 * 60, label: ''}];
    for (const range of ranges) {
        const line = document.createElement('div');
        line.style.overflowWrap = 'anywhere';
        const prefix = concertOverride ? 'Today (Concert Day): ' : range.label ? `${range.label}: ` : '';
        line.textContent = `${prefix}${formatTime(range.start)} - ${formatTime(range.end)}`;
        hoursElem.appendChild(line);
    }
    // These existing messages are Wagtail editor-authored rich text. Period labels
    // and concert names above are plain text and never enter this HTML boundary.
    if (visitTextElem) visitTextElem.innerHTML = concertOverride ? '' : schedule.additional_message || '';
    if (emphaticTextElem) emphaticTextElem.innerHTML = concertOverride ? '' : schedule.additional_emphatic_mesg || '';
    displayOpenClosed(ranges.some((range) => today.minutes >= range.start && today.minutes < range.end), schedule);
}

async function refreshGardenHours() {
    const hours = await getGardenHours();
    setHours(hours);
}

if (pageID && hoursElem) {
    window.addEventListener('load', refreshGardenHours);
    setInterval(refreshGardenHours, 300000);
}
