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

function expandBigListForm(){
    const form = document.querySelector('.big-list-form');
    
    if (form.getAttribute('data-expanded') === 'false') {
        form.style.transform = "translate(50%, 0%)";
        form.setAttribute('data-expanded', 'true');
    } else {
        form.style.transform = "translate(50%, 100%)";
        form.setAttribute('data-expanded', 'false');
    }
}

function expandModifyOverlay(itemID){
    const overlay = document.querySelector(`#edit-overlay-${itemID}`);
    if (overlay.getAttribute('data-expanded') === 'false') {
        overlay.style.transform = "translate(-50%, -50%)";
        overlay.setAttribute('data-expanded', 'true');
    } else {
        overlay.style.transform = "translate(-50%, 50%)";
        overlay.setAttribute('data-expanded', 'false');
    }
}