/*
Looks for image links with a parent of class "hidden" and "child-page". Script will move this element into the list
of proper Wagtail child pages so everything looks the same.
 */

function matchChildren() {
    const wagtailList = document.getElementById("wagtail-children");

    [].forEach.call(document.getElementsByClassName('hidden child-page'), function (child) {
        wagtailList.appendChild(child);
        child.classList.remove("hidden", "child-page");
        child.classList.add("col-sm-4");
    })
}

window.onload = matchChildren;
