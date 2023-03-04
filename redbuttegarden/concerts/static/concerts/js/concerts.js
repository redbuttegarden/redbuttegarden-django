const waveInfoBanners = document.getElementsByClassName('wave-info');

if (waveInfoBanners.length > 0) {
    const waveTwoBanners = document.getElementsByClassName('wave-two-banner');

    [].forEach.call(waveTwoBanners, (element) => {
        let concert = element.closest('.concertwrapper');
        concert.style.opacity = '0.65';

        let buyButton = concert.getElementsByClassName('con-button')[0];
        buyButton.className = 'responsive';
        let buttonParent = buyButton.parentElement;

        let disableDiv = document.createElement('div');
        disableDiv.className = 'disable-buy';
        disableDiv.replaceChildren(...buttonParent.childNodes);

        buttonParent.replaceWith(disableDiv);
    });
}
