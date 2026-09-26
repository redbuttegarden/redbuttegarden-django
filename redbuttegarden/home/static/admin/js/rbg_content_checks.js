/** Register the Red Butte Garden ambiguous-link content check. */
customElements.whenDefined("wagtail-userbar").then(() => {
    const userbar = document.querySelector("wagtail-userbar");
    if (!userbar || typeof userbar.registerCheck !== "function") return;

    userbar.registerCheck("check-rbg-link-text", (node, options) => {
        const linkText = node.textContent.replace(/\s+/g, " ").trim();
        const antipattern = new RegExp(options.antipattern, "i");
        return !antipattern.test(linkText);
    });
});
