const conditionElem = document.getElementById('weatherConditions');
const tempElem = document.getElementById('weatherTemp');

const updateWeather = async () => {
    const response = await fetch('api/latest-weather',
        {
            method: 'GET',
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        });
    const weatherJSON = await response.json(); //extract JSON from the http response
    conditionElem.textContent = weatherJSON['condition'];
    tempElem.textContent = weatherJSON['temperature'];
}

updateWeather()
setInterval(updateWeather, 902000); // Update weather every ~15 minutes
