function admissionHoverOn() {
    const rbgAdmissionHidden = document.getElementById('rbgadmission2');
    const rbgAdmission = document.getElementById('rbgadmission');
    rbgAdmission.innerHTML = rbgAdmissionHidden.innerHTML;
    rbgAdmission.classList.remove('rbgadmission');
}
