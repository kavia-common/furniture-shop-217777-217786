from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..models import Product, ProductListResponse, ProductQuery
from ..services import get_product_by_id, list_products

router = APIRouter(prefix="/products", tags=["products"])


def parse_product_query(
    q: Optional[str] = Query(None, description="Search query on name and description"),
    category: Optional[str] = Query(None, description="Filter by category, exact match"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(12, ge=1, le=100, description="Items per page"),
) -> ProductQuery:
    """
    Parse and validate product query params into ProductQuery model.
    """
    return ProductQuery(
        q=q,
        category=category,
        min_price=min_price,
        max_price=max_price,
        page=page,
        page_size=page_size,
    )


# PUBLIC_INTERFACE
@router.get(
    "",
    summary="List products",
    description="Returns a paginated list of products with optional search and filters.",
    operation_id="list_products",
    response_model=ProductListResponse,
)
def get_products(query: ProductQuery = Depends(parse_product_query)) -> ProductListResponse:
    """
    List products applying optional filters and pagination.
    """
    # Validate price range
    if query.min_price is not None and query.max_price is not None and query.min_price > query.max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price cannot be greater than max_price",
        )

    items, total = list_products(query)
    return ProductListResponse(items=items, total=total, page=query.page, page_size=query.page_size)


# PUBLIC_INTERFACE
@router.get(
    "/{product_id}",
    summary="Get product by ID",
    description="Returns a single product by its identifier.",
    operation_id="get_product_by_id",
    response_model=Product,
    responses={
        404: {"description": "Product not found"},
    },
)
def get_product(product_id: int) -> Product:
    """
    Fetch a single product by ID, returning 404 if not found.
    """
    product = get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product
