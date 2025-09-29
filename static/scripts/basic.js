let formLocked = false;

function expandListForm(cssClass) {
    if (formLocked){
        return;
    }

    // const button = document.querySelector('.create-space-button');
    const form = document.querySelector('.' + cssClass);

    
    if (form.getAttribute('data-expanded') === 'false') {
        form.style.transform = "translate(50%, 0%)";
        form.setAttribute('data-expanded', 'true');
    } else {
        form.style.transform = "translate(50%, 100%)";
        form.setAttribute('data-expanded', 'false');
    }
}

function expandBigListForm(){
    if (formLocked){
        return;
    }

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

  formLocked = true;

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
      addShoppingListItemToDOM(data.item, false);
      input.value = "";
    } else {
      console.error("Error:", data.message);
    }
  })
  .catch(err => console.error("Request failed", err))
  .finally(() => {
    formLocked = false;
  });
}

function addShoppingListItemToDOM(item, smart_add) {
  const list = document.querySelector(".shopping-list");
  const card = document.createElement("div");
  card.classList.add("item-card", "list-item-card");
  card.id = `shopping-list-item-${item.list_item_id}`;

  if (smart_add) {
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
        <div class="item-card-info list-item-info smart-add-info">
            <div class="smart-add-icon-wrap">    
                <span class="material-symbols-rounded">bolt</span>
            </div>
            <div class="smart-add-info-text">
                added smartly
            </div>
        </div>
    `;
  } else {
    card.innerHTML = `<div class="space-icon-and-name list-item-main">
        <a class="item-card-checkbox list-item-icon"
            id="item-card-checkbox-${item.list_item_id}"
            data-checked="false"
            onmousedown="checkShoppingListItem(${item.list_item_id})">
            <div class="item-card-checkbox-filling"></div>
        </a>
        <div class="item-card-name list-item-name">${item.product_name}</div>
        </div>
        <div class="item-card-info list-item-info">added now</div>`;
  }

  list.appendChild(card);

  formLocked = false;

  if (!smart_add) {
    expandListForm('shopping-list-form');
  }
}

function addItemToSpace(e) {
    e.preventDefault(); // blockiert Standard-Submit

    const name = document.querySelector("#space_item_name").value.trim();
    const expiration = document.querySelector("#expiration_date").value || null;
    const amount = document.querySelector("#amount").value.trim();
    const unit = document.querySelector("#unit").value;

    if (!name || !amount || !unit) return false;

    formLocked = true;

    fetch("/api/add-to-space-list", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        body: JSON.stringify({
            item_name: name,
            expiration_date: expiration,
            amount: amount,
            unit: unit
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            addSpaceItemToDOM(data.item);
            // Reset Form
            document.querySelector("#space_item_name").value = "";
            document.querySelector("#expiration_date").value = "";
            document.querySelector("#amount").value = "";
            document.querySelector("#unit").selectedIndex = 0;
        } else {
            console.error("Error:", data.message);
        }
    })
    .catch(err => console.error("Request failed", err))
    .finally(() => formLocked = false);
}

function addSpaceItemToDOM(item) {
    const grid = document.querySelector(".item-tiles");

    const tile = document.createElement("div");
    tile.classList.add("tile", "item-tile");

    tile.innerHTML = `
      <div class="tile-content" onmousedown="expandModifyOverlay(${item.id})">
        <div class="tile-icon">
          <span class="material-symbols-rounded">grocery</span>
        </div>
        <div class="tile-name">${item.name}</div>
        <div class="tile-info">
          <div class="tile-info-tag important-tag">
            ${item.readable_expiration_date ? "exp. " + item.readable_expiration_date : "exp. unset"}
          </div>
          <div class="tile-info-tag semi-important-tag">
            ${item.quantity} ${item.unit}
          </div>
        </div>
      </div>

      <div class="modify-overlay" id="edit-overlay-${item.id}" data-expanded="false">
        <form onsubmit="return modifyItemAmount(event, ${item.id})">
          <label for="amount" class="helper-label">New Amount</label>
          <input type="number" placeholder="New Amount" name="amount" value="${item.quantity}" min="0" required>
          <button>Modify</button>
        </form>
      </div>
    `;

    grid.appendChild(tile);

    formLocked = false;
    expandBigListForm();
}

function modifyItemAmount(e, itemID) {
    e.preventDefault();

    const input = e.target.querySelector("input[name='amount']");
    const newAmount = Number(input.value);
    if (isNaN(newAmount) || newAmount < 0) return false;

    formLocked = true;

    fetch(`/api/modify-item-amount/${itemID}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        body: JSON.stringify({ amount: newAmount })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            updateItemTileDOM(data.item);
        } else {
            console.error("Modify failed:", data.message);
        }
    })
    .catch(err => console.error("Request failed", err))
    .finally(() => formLocked = false);

    formLocked = false;
    expandModifyOverlay(itemID);
}

function updateItemTileDOM(item) {
    const tile = document.querySelector(`.item-tile .tile-content[onmousedown*="expandModifyOverlay(${item.id})"]`);
    if (!tile) return;

    const quantityInt = parseInt(item.quantity, 10);

    if (quantityInt === 0) {
        // hide element
        const tileElement = tile.closest('.item-tile');
        if (tileElement) tileElement.style.display = "none";

        // add to shopping list automatically
        fetch('/api/smart-add-shopping-list', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            body: JSON.stringify({ item_name: item.name })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                addShoppingListItemToDOM(data.item, true);
            } else {
                console.error("Failed to add to shopping list:", data.message);
            }
        })
        .catch(err => console.error("Request failed", err));

        return;
    }

    tile.querySelector(".amount-info-tag").textContent = `${quantityInt} ${item.unit}`;

    /*const dateDiv = tile.querySelector(".tile-date");
    if (dateDiv) {

        dateDiv.textContent = item.readable_expiration_date ? `expires ${item.readable_expiration_date}` : "no expiration date";
    }*/
}

function focusSpacesList(){
    // highlight spaces list, .spaces-list for 1s, then remove class
    document.querySelector('.spaces').classList.add('focus');
    setTimeout(() => {
        console.log('timeout');
        document.querySelector('.spaces').classList.remove('focus');
    }, 1000);
    return;
}

function openInviteMenu(){
    // request api/create-invitation with deault space id of 2 for testing
    formLocked = true;
    fetch('/api/create-invitation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
        body: JSON.stringify({
            space_id: 2
        }),
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
    })
    .catch(err => console.error('Request failed', err))
    .finally(() => formLocked = false);
}

document.getElementById("create-invite-form").addEventListener("submit", function(e) {
    e.preventDefault();
    const spaceId = document.getElementById("space").value;

    expandListForm('create-invite-form');
    formLocked = true;
    document.getElementById("qa-invite").innerHTML = "Creating Invite...";

    fetch("/api/create-invitation", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        body: JSON.stringify({ space_id: spaceId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            addInviteMessage(data.invitation.code, spaceId);
        } else {
            alert("Error: " + data.message);
        }
    })
    .catch(err => console.error("Request failed", err))
    .finally(() => {
        formLocked = false;
        document.getElementById("qa-invite").innerHTML = "Invite";
    });
});

function addInviteMessage(code, spaceId) {
    const overview = document.querySelector(".child.overview");

    // die "no messages" Info ausblenden
    const noMsg = overview.querySelector(".no-messages-text");
    if (noMsg) noMsg.style.display = "none";

    // neues Message Element
    const msg = document.createElement("div");
    msg.classList.add("message", "info");
    msg.innerHTML = `
        <div class="message-icon">
            <span class="material-symbols-rounded">mail_shield</span>
        </div>
        <div class="message-text">
            Invite created. Code to share: 
            <code>${code}</code>
            <a class="copy-btn">(Copy Code)</a>
        </div>
    `;

    // copy handler
    msg.querySelector(".copy-btn").addEventListener("click", () => {
        navigator.clipboard.writeText(code)
            .then(() => {
                msg.querySelector(".copy-btn").textContent = "(Copied!)";
                setTimeout(() => {
                    msg.querySelector(".copy-btn").textContent = "(Copy)";
                }, 1500);
            })
            .catch(err => console.error("Clipboard error:", err));
    });

    // ganz oben einfügen
    overview.prepend(msg);
}

// join space via invite
document.getElementById("join-space-form").addEventListener("submit", function(e) {
    e.preventDefault();
    const code = document.getElementById("invitation_code").value.trim();

    expandListForm('join-space-form');
    formLocked = true;
    document.getElementById("qa-join").innerHTML = "Joining...";

    fetch("/api/handle-invitation", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        body: JSON.stringify({ invitation_code: code })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert("Joined space successfully!");
            location.reload();
        } else {
            alert("Error: " + data.message);
        }
    })
    .catch(err => console.error("Request failed", err))
    .finally(() => {
        formLocked = false;
        document.getElementById("qa-join").innerHTML = "Join Space";
    });
});
