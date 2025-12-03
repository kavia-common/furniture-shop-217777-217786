from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException, status

from ..models import Product, WishlistResponse
from ..services import get_product_by_id
from ..wishlist_store import add_to_wishlist, get_wishlist_ids, remove_from_wishlist

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


def get_user_id(x_user_id: str | None = Header(default=None, alias="X-User-Id")) -> str:
    """
    Resolve the user id from the X-User-Id header.

    For this demo, the frontend will generate and persist a random id in localStorage
    and send it along with every request. We require it to scope wishlists per-user.
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-User-Id header is required",
        )
    return x_user_id


# PUBLIC_INTERFACE
@router.get(
    "",
    summary="Get wishlist",
    description="Returns the current user's wishlist as a list of full Product objects. Requires X-User-Id header.",
    operation_id="get_wishlist",
    response_model=WishlistResponse,
)
def get_wishlist(user_id: str = Depends(get_user_id)) -> WishlistResponse:
    """
    Fetch the list of products in the user's wishlist.
    """
    ids = get_wishlist_ids(user_id)
    items: List[Product] = []
    for pid in ids:
        p = get_product_by_id(pid)
        if p:
            items.append(p)
    return WishlistResponse(items=items)


# PUBLIC_INTERFACE
@router.post(
    "/{product_id}",
    summary="Add product to wishlist",
    description="Adds a product to the user's wishlist by product id. Requires X-User-Id header.",
    operation_id="add_to_wishlist",
    responses={
        204: {"description": "Added to wishlist"},
        404: {"description": "Product not found"},
    },
    status_code=204,
)
def add(product_id: int, user_id: str = Depends(get_user_id)) -> None:
    """
    Add a product to the wishlist. Returns 404 if the product does not exist.
    """
    product = get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    add_to_wishlist(user_id, product_id)
    return None


# PUBLIC_INTERFACE
@router.delete(
    "/{product_id}",
    summary="Remove product from wishlist",
    description="Removes a product from the user's wishlist by product id. Requires X-User-Id header.",
    operation_id="remove_from_wishlist",
    responses={
        204: {"description": "Removed from wishlist"},
    },
    status_code=204,
)
def remove(product_id: int, user_id: str = Depends(get_user_id)) -> None:
    """
    Remove a product from the wishlist. No error if product is not in the wishlist.
    """
    remove_from_wishlist(user_id, product_id)
    return None
