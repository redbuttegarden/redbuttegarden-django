/*
Addresses the problem where an event index page will display the message "There are currently no planned events in the
near future. Please check back soon!" if there are no child pages even if there are page_link blocks that link to events
that are children of some other index page.

This script simply hides the "no events" message if a page_link is present on the page.
*/
if ($(".page-link")[0]) {
    // At least one page_link object exists on the page
    $("#empty-msg").hide();  // hide the div containing the empty message
}