/*
Looks for image links with a parent of class "hidden" and "child-page". Script will move this element into the list
of proper Wagtail child pages so everything looks the same.
 */

function matchChildren() {
    const wagtailList = document.getElementById("wagtail-children");

    [].forEach.call(document.getElementsByClassName('d-none child-page'), function (child) {
        wagtailList.appendChild(child);
        child.classList.remove("d-none", "child-page");
        child.classList.add("index-tile");
    })
}

window.onload = matchChildren;
