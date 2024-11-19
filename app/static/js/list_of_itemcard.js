async function updateQuantity(itemId, action) {
    const userId = {{ user_id }};
    try {
        const response = await fetch(`/webapp/api/cart/update_quantity`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: userId, item_id: itemId, action }),
        });

        const data = await response.json();
        if (response.ok) {
            const quantitySpan = document.querySelector(`.quantity-span[data-item-id="${itemId}"]`);
            const decreaseBtn = document.querySelector(`.decrease-btn[data-item-id="${itemId}"]`);

            if (data.quantity > 0) {
                quantitySpan.style.display = "inline";
                decreaseBtn.style.display = "inline";
                quantitySpan.innerText = data.quantity;
            } else {
                quantitySpan.style.display = "none";
                decreaseBtn.style.display = "none";
                await removeItemFromCart(itemId);
            }
        } else {
            console.error("Ошибка:", data.detail || "Не удалось обновить количество");
        }
    } catch (error) {
        console.error("Ошибка при обновлении количества:", error);
    }
}

async function removeItemFromCart(itemId) {
    const userId = {{ user_id }};
    try {
        const response = await fetch(`/webapp/api/cart/remove_item`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: userId, item_id: itemId }),
        });

        if (!response.ok) {
            console.error("Ошибка при удалении товара:", await response.json());
        }
    } catch (error) {
        console.error("Ошибка при удалении товара:", error);
    }
}

document.querySelectorAll(".increase-btn").forEach((button) => {
    button.addEventListener("click", () => {
        const itemId = parseInt(button.dataset.itemId, 10);
        updateQuantity(itemId, "increase");
    });
});

document.querySelectorAll(".decrease-btn").forEach((button) => {
    button.addEventListener("click", () => {
        const itemId = parseInt(button.dataset.itemId, 10);
        updateQuantity(itemId, "decrease");
    });
});
