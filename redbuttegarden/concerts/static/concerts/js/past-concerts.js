const colorOptions = [
    "#CF7B4E",
    "#171D32",
    "#172843",
    "#BDC0C7",
    "#526FA8",
    "#5BBBE2",
    "#94A050",
    "#200A35",
    "#53A8A3",
    "#4F3F35",
    "#E6C378",
    "#6A3A86",
    "#8C302F"
];

function getRandomColor() {
    const random = Math.floor(Math.random() * colorOptions.length);
    return colorOptions[random];
}

const posters = document.getElementById("poster-holder").children;

for (let i = 0; i < posters.length; i++) {
    const posterOuterDiv = document.getElementById("poster-outer-" + i);
    const posterInnerMostDiv = document.getElementById("innermost-" + i);

    posterOuterDiv.style.backgroundColor = getRandomColor();
    posterInnerMostDiv.style.backgroundColor = getRandomColor();
}
