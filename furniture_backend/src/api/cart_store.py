from typing import Dict, Any

# In-memory cart storage: user_id -> {product_id -> {'quantity': int}}
_CARTS: Dict[str, Dict[int, Dict[str, Any]]] = {}


def _get_cart(user_id: str) -> Dict[int, Dict[str, Any]]:
    if user_id not in _CARTS:
        _CARTS[user_id] = {}
    return _CARTS[user_id]


# PUBLIC_INTERFACE
def add_to_cart(user_id: str, product_id: int, quantity: int = 1) -> None:
    """
    Add (or increment) a product in the user's cart. Minimum quantity = 1.
    """
    cart = _get_cart(user_id)
    if product_id in cart:
        cart[product_id]['quantity'] += max(1, quantity)
    else:
        cart[product_id] = {'quantity': max(1, quantity)}


# PUBLIC_INTERFACE
def set_cart_quantity(user_id: str, product_id: int, quantity: int) -> None:
    """
    Set the quantity of a product in the cart. Removes it if quantity < 1.
    """
    cart = _get_cart(user_id)
    if quantity < 1:
        cart.pop(product_id, None)
    else:
        cart[product_id] = {'quantity': quantity}


# PUBLIC_INTERFACE
def remove_from_cart(user_id: str, product_id: int) -> None:
    """
    Remove a product from the cart.
    """
    cart = _get_cart(user_id)
    cart.pop(product_id, None)


# PUBLIC_INTERFACE
def clear_cart(user_id: str) -> None:
    """
    Remove all products from the user's cart.
    """
    _CARTS[user_id] = {}


# PUBLIC_INTERFACE
def get_cart_items(user_id: str) -> Dict[int, Dict[str, Any]]:
    """
    Return the dict of product_id -> {quantity: int} in the user's cart.
    """
    return dict(_get_cart(user_id))
