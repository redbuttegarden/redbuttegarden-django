let alerts = document.getElementsByClassName('alert');
const mainElem = document.getElementById('main');

/*
When an alert is dismissed, the element is completely removed from the page structure.
If a keyboard user dismisses the alert using the close button, their focus will suddenly
be lost and, depending on the browser, reset to the start of the page/document. For this
reason, we recommend including additional JavaScript that listens for the closed.bs.alert
event and programmatically sets focus() to the most appropriate location in the page.

https://getbootstrap.com/docs/5.3/components/alerts/
 */
Array.from(alerts).forEach(alert => {
    alert.addEventListener('closed.bs.alert', (event) => {
        mainElem.focus();
    });
});