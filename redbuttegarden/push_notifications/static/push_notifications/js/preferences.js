/** Manage explicit Web Push opt-in and opt-out on the preferences page. */
(function () {
    const status = document.getElementById("push-preferences-status");
    const enableButton = document.getElementById("enable-push");
    const disableButton = document.getElementById("disable-push");
    const keyElement = document.getElementById("push-vapid-public-key");

    function announce(message) {
        status.textContent = message;
    }

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        return parts.length === 2 ? parts.pop().split(";").shift() : "";
    }

    function urlBase64ToUint8Array(value) {
        const padded = value + "=".repeat((4 - value.length % 4) % 4);
        const base64 = padded.replace(/-/g, "+").replace(/_/g, "/");
        return Uint8Array.from(atob(base64), (character) => character.charCodeAt(0));
    }

    async function sendSubscription(method, subscription) {
        const response = await fetch("/push/subscriptions/", {
            method,
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify(method === "DELETE" ? { endpoint: subscription.endpoint } : subscription),
        });
        if (!response.ok) throw new Error("The preference could not be saved.");
    }

    async function enable() {
        const publicKey = keyElement ? JSON.parse(keyElement.textContent) : "";
        if (!publicKey) {
            announce("Notifications are not configured yet. Please try again later.");
            return;
        }
        const registration = await navigator.serviceWorker.ready;
        const permission = await Notification.requestPermission();
        if (permission !== "granted") {
            announce("Notifications are not enabled. You can change this in your browser settings.");
            return;
        }
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(publicKey),
        });
        await sendSubscription("POST", subscription);
        announce("Notifications are enabled for this browser.");
    }

    async function disable() {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.getSubscription();
        if (!subscription) {
            announce("Notifications are already disabled for this browser.");
            return;
        }
        await sendSubscription("DELETE", subscription);
        await subscription.unsubscribe();
        announce("Notifications are disabled for this browser.");
    }

    if (!("serviceWorker" in navigator && "PushManager" in window && "Notification" in window)) {
        enableButton.disabled = true;
        disableButton.disabled = true;
        announce("This browser does not support push notifications.");
        return;
    }
    enableButton.addEventListener("click", () => enable().catch(() => announce("Notifications could not be enabled. Please try again.")));
    disableButton.addEventListener("click", () => disable().catch(() => announce("Notifications could not be disabled. Please try again.")));
}());
