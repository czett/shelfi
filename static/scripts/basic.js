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

function clearShoppingList(){
    let shoppingList = document.querySelector('.shopping-list');
    let apiTarget = '/api/clear-shopping-list';

    // for every .item-card in shopping list, if it has the .checked-list-item class, remove it from dom
    for (let i = 0; i < shoppingList.children.length; i++) {
        let child = shoppingList.children[i];
        if (child.classList.contains('checked-list-item')) {
            shoppingList.removeChild(child);
        }
    }

    // call api route
    fetch(apiTarget, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
        body: JSON.stringify({}),
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
    })
}

function checkShoppingListItem(itemID){
    let checkbox = document.getElementById(`item-card-checkbox-${itemID}`);
    checkbox.setAttribute('data-checked', !checkbox.getAttribute('data-checked'));

    let itemCard = document.getElementById(`shopping-list-item-${itemID}`);
    /*if (checkbox.getAttribute('data-checked') === 'true') {
        itemCard.classList.add('checked-list-item');
    } else {
        itemCard.classList.remove('checked-list-item');
    }*/

    itemCard.classList.toggle('checked-list-item');

    // call api route
    fetch(`/api/toggle-shopping-list-item/${itemID}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
        body: JSON.stringify({}),
    })
}

function addItem(e) {
  e.preventDefault();

  const input = document.querySelector("#item_name");
  const itemName = input.value.trim();
  if (!itemName) return false;

  fetch("/api/add-item-to-shopping-list", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json"
    },
    body: JSON.stringify({ item_name: itemName })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      addShoppingListItemToDOM(data.item);
      input.value = "";
    } else {
      console.error("Error:", data.message);
    }
  })
  .catch(err => console.error("Request failed", err));

  return false;
}

function addShoppingListItemToDOM(item) {
  const list = document.querySelector(".shopping-list");
  const card = document.createElement("div");
  card.classList.add("item-card", "list-item-card");
  card.id = `shopping-list-item-${item.list_item_id}`;

  card.innerHTML = `
    <div class="space-icon-and-name list-item-main">
      <a class="item-card-checkbox list-item-icon"
         id="item-card-checkbox-${item.list_item_id}"
         data-checked="false"
         onmousedown="checkShoppingListItem(${item.list_item_id})">
        <div class="item-card-checkbox-filling"></div>
      </a>
      <div class="item-card-name list-item-name">${item.product_name}</div>
    </div>
    <div class="item-card-info list-item-info">
      added by <span style="font-weight: 700;">@${item.username}</span> on ${item.created_at}
    </div>
  `;

  list.appendChild(card);

  expandListForm();
}
