from fastapi import APIRouter, Depends, Header, HTTPException, Path, status, Body

from ..models import CartResponse, CartItem, UpdateQuantityRequest
from ..services import get_product_by_id
from ..cart_store import (
    add_to_cart,
    set_cart_quantity,
    remove_from_cart,
    clear_cart,
    get_cart_items,
)


router = APIRouter(prefix="/cart", tags=["cart"])


def get_user_id(x_user_id: str | None = Header(default=None, alias="X-User-Id")) -> str:
    """
    Resolve the user id from the X-User-Id header.

    Required for user cart scoping.
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-User-Id header is required",
        )
    return x_user_id


def _build_cart_response(user_id: str) -> CartResponse:
    """
    Helper: Build CartResponse for the given user's cart items.
    """
    items = []
    total = 0.0
    for pid, entry in get_cart_items(user_id).items():
        product = get_product_by_id(pid)
        if not product:
            continue
        quantity = max(1, entry.get("quantity", 1))
        price = product.price
        subtotal = quantity * price
        items.append(
            CartItem(product=product, quantity=quantity, price=price, subtotal=subtotal)
        )
        total += subtotal
    return CartResponse(items=items, total=total)


# PUBLIC_INTERFACE
@router.get(
    "",
    summary="Get cart",
    description="Returns the user's cart: items with quantity, price, subtotal, and total. Requires X-User-Id header.",
    response_model=CartResponse,
    operation_id="get_cart",
)
def get_cart(user_id: str = Depends(get_user_id)) -> CartResponse:
    """
    Returns full cart details for the user, including quantities, prices, subtotals, and total.
    """
    return _build_cart_response(user_id)


# PUBLIC_INTERFACE
@router.post(
    "/{product_id}",
    summary="Add/increment product in cart",
    description="Add or increment a product in the user's cart. Body: {quantity: int = 1}. Requires X-User-Id header.",
    status_code=204,
    operation_id="add_to_cart",
)
def add_or_increment_cart(
    product_id: int = Path(..., description="Product ID to add/increment in cart"),
    body: dict = Body({}, example={"quantity": 1}),
    user_id: str = Depends(get_user_id),
) -> None:
    """
    Add or increment a product's quantity in the cart. If not present, adds it.
    """
    quantity = int(body.get("quantity", 1))
    if quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")
    product = get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    add_to_cart(user_id, product_id, quantity)
    return None


# PUBLIC_INTERFACE
@router.patch(
    "/{product_id}",
    summary="Set product quantity in cart",
    description="Set the quantity of a product in the cart (replace value). Removes if quantity < 1. Requires X-User-Id header.",
    status_code=204,
    operation_id="set_cart_quantity",
)
def patch_cart_quantity(
    product_id: int = Path(..., description="Product ID"),
    req: UpdateQuantityRequest = Body(...),
    user_id: str = Depends(get_user_id),
) -> None:
    """
    Update the quantity of a specific cart product (set, not increment).
    """
    product = get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    set_cart_quantity(user_id, product_id, req.quantity)
    return None


# PUBLIC_INTERFACE
@router.delete(
    "/{product_id}",
    summary="Remove product from cart",
    description="Removes a product from the cart by id. Requires X-User-Id header.",
    status_code=204,
    operation_id="remove_from_cart",
)
def remove_cart_item(
    product_id: int = Path(..., description="Product ID"),
    user_id: str = Depends(get_user_id),
) -> None:
    """
    Remove an item from the user's cart. No error if not present.
    """
    remove_from_cart(user_id, product_id)
    return None


# PUBLIC_INTERFACE
@router.delete(
    "",
    summary="Clear cart",
    description="Removes all products from the user's cart. Requires X-User-Id header.",
    status_code=204,
    operation_id="clear_cart",
)
def clear_cart_items(user_id: str = Depends(get_user_id)) -> None:
    """
    Remove all items from the user's cart.
    """
    clear_cart(user_id)
    return None
