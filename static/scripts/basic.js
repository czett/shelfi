function expandListForm() {
    // const button = document.querySelector('.create-space-button');
    const form = document.querySelector('.list-form');

    
    if (form.getAttribute('data-expanded') === 'false') {
        form.style.transform = "translate(50%, 0%)";
        form.setAttribute('data-expanded', 'true');
    } else {
        form.style.transform = "translate(50%, 100%)";
        form.setAttribute('data-expanded', 'false');
    }
}