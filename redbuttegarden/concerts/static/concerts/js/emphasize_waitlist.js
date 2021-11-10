$("div.sponinfo > table > caption").each(function () {
    const words = this.innerText.split(" ");
    for (let i = 0; i < words.length; i++) {
        if (words[i] === "Waitlist") {
            this.innerHTML = this.innerHTML.replace(words[i], '<span class="red">' + words[i] + '</span>');
        }
    }
});