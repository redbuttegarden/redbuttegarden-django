/*
This script automatically sets the seasonal banner image for the What's Blooming Now Blog
 */

const bannerDiv = document.getElementById('journal-banner').firstElementChild;

// JS Seasonal determination taken from https://stackoverflow.com/a/54501026
// Credit to kornieff: https://stackoverflow.com/users/3094153/kornieff
const md = (month, day) => ({month, day})
const toMd = date => md(date.getMonth(), date.getDate())

const before = (md1, md2) => (md1.month < md2.month)
    || ((md1.month === md2.month) && (md1.day <= md2.day))

const after = (md1, md2) => !before(md1, md2)

const between = (mdX, mdLow, mdHigh) =>
    after(mdX, mdLow) && before(mdX, mdHigh)

const season = (date, seasons) => ((md = toMd(date)) =>
        Object.keys(seasons).find(season => seasons[season](md))
)()

const MARCH_EQUINOX = md(2, 20)
const JUNE_SOLSTICE = md(5, 20)
const SEPTEMBER_EQUINOX = md(8, 22)
const DECEMBER_SOLSTICE = md(11, 20)
const NEW_YEAR = md(0, 1)

const seasons = {
    spring: d => between(d, MARCH_EQUINOX, JUNE_SOLSTICE),
    summer: d => between(d, JUNE_SOLSTICE, SEPTEMBER_EQUINOX),
    fall: d => between(d, SEPTEMBER_EQUINOX, DECEMBER_SOLSTICE),
    winter: d =>
        between(d, DECEMBER_SOLSTICE, NEW_YEAR) ||
        between(d, NEW_YEAR, MARCH_EQUINOX)
}

const todaysDate = new Date();

function getSeasonalBanner(season) {
    switch (season) {
        case 'spring':
            return 'https://redbuttegarden.org/media/images/whats-blooming-now-spring.original.jpg'
        case 'summer':
            return 'https://redbuttegarden.org/media/images/whats-blooming-now-summer.original.jpg'
        case 'fall':
            return 'https://redbuttegarden.org/media/images/whats-blooming-now-fall.original.jpg'
        case 'winter':
            return 'https://redbuttegarden.org/media/images/whats-blooming-now-winter.original_w6thquA.jpg'
    }
}

function setSeasonalBanner(calculatedSeason) {
    console.log(
        'It is currently',
        calculatedSeason,
        'in northern hemisphere on 4 season astronomical calendar'
    )
    if (typeof calculatedSeason !== "undefined") {
        // Clear any existing banner image in the parent banner div
        bannerDiv.innerHTML = '';
        const bannerImage = document.createElement("img");
        bannerImage.setAttribute("src", getSeasonalBanner(calculatedSeason));
        bannerImage.setAttribute("alt", "Seasonal banner for What's Blooming Now Blog");
        bannerImage.setAttribute("height", "100");
        bannerImage.setAttribute("width", "1280");
        bannerDiv.appendChild(bannerImage);
    }
}

setSeasonalBanner(season(todaysDate, seasons));