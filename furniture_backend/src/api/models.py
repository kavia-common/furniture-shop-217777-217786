from typing import List, Optional
from pydantic import BaseModel, Field


# PUBLIC_INTERFACE
class Product(BaseModel):
    """Represents a furniture product in the catalog."""
    id: int = Field(..., description="Unique identifier of the product")
    name: str = Field(..., description="Name of the product")
    description: str = Field(..., description="Detailed description of the product")
    price: float = Field(..., ge=0, description="Price of the product")
    category: str = Field(..., description="Category of the product (e.g., 'Sofa', 'Chair')")
    image_url: Optional[str] = Field(None, description="URL to a product image")


# PUBLIC_INTERFACE
class ProductListResponse(BaseModel):
    """Paginated response for a list of products."""
    items: List[Product] = Field(..., description="List of products for the current page")
    total: int = Field(..., ge=0, description="Total number of products matching the query")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Number of items per page")


# PUBLIC_INTERFACE
class ProductQuery(BaseModel):
    """Query parameters for filtering and paginating product results."""
    q: Optional[str] = Field(None, description="Search query to match product name or description")
    category: Optional[str] = Field(None, description="Filter by category")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price filter")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price filter")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(12, ge=1, le=100, description="Items per page (max 100)")


# PUBLIC_INTERFACE
class WishlistResponse(BaseModel):
    """Represents the wishlist for a user as a list of full Product objects."""
    items: List[Product] = Field(..., description="Products currently in the user's wishlist")
