from typing import Dict, Set

# Simple in-memory wishlist store keyed by user_id -> set(product_id)
# Note: This is ephemeral and per-process; suitable for demo/dev only.
_WISHLISTS: Dict[str, Set[int]] = {}


def _get_set(user_id: str) -> Set[int]:
    if user_id not in _WISHLISTS:
        _WISHLISTS[user_id] = set()
    return _WISHLISTS[user_id]


# PUBLIC_INTERFACE
def add_to_wishlist(user_id: str, product_id: int) -> None:
    """Add a product to the user's wishlist."""
    _get_set(user_id).add(product_id)


# PUBLIC_INTERFACE
def remove_from_wishlist(user_id: str, product_id: int) -> None:
    """Remove a product from the user's wishlist if present."""
    _get_set(user_id).discard(product_id)


# PUBLIC_INTERFACE
def get_wishlist_ids(user_id: str) -> Set[int]:
    """Return the set of product IDs in the user's wishlist."""
    return set(_get_set(user_id))
