from typing import List, Optional, Tuple

from .models import Product, ProductQuery


# Seed in-memory product catalog for initial development.
# In a real application, replace with database integration.
_PRODUCTS: List[Product] = [
    Product(
        id=1,
        name="Ocean Blue Sofa",
        description="A modern three-seater sofa with plush cushions and durable fabric.",
        price=899.99,
        category="Sofa",
        image_url="https://images.unsplash.com/photo-1549187774-b4e9b0445b41?q=80&w=1280&auto=format&fit=crop",
    ),
    Product(
        id=2,
        name="Amber Accent Chair",
        description="Ergonomic accent chair with amber upholstery for a pop of color.",
        price=249.50,
        category="Chair",
        image_url="https://images.unsplash.com/photo-1549497539-91dfc646d0f1?q=80&w=1280&auto=format&fit=crop",
    ),
    Product(
        id=3,
        name="Minimalist Coffee Table",
        description="Low-profile coffee table with oak veneer and rounded corners.",
        price=179.00,
        category="Table",
        image_url="https://images.unsplash.com/photo-1555041469-a586c61ea9bc?q=80&w=1280&auto=format&fit=crop",
    ),
    Product(
        id=4,
        name="Ergo Office Chair",
        description="Adjustable office chair with lumbar support and breathable mesh.",
        price=329.00,
        category="Chair",
        image_url="https://images.unsplash.com/photo-1582582621957-820c1f47e109?q=80&w=1280&auto=format&fit=crop",
    ),
    Product(
        id=5,
        name="Scandinavian Dining Set",
        description="Dining table with four chairs, light wood finish, and clean lines.",
        price=1199.00,
        category="Dining",
        image_url="https://images.unsplash.com/photo-1519710164239-da123dc03ef4?q=80&w=1280&auto=format&fit=crop",
    ),
    Product(
        id=6,
        name="Floating Wall Shelf",
        description="Wall-mounted shelf, white lacquer finish, ideal for decor.",
        price=59.99,
        category="Storage",
        image_url="https://images.unsplash.com/photo-1484154218962-a197022b5858?q=80&w=1280&auto=format&fit=crop",
    ),
]


def _matches_query(p: Product, q: Optional[str]) -> bool:
    if not q:
        return True
    q_lower = q.lower()
    return q_lower in p.name.lower() or q_lower in p.description.lower()


def _matches_category(p: Product, category: Optional[str]) -> bool:
    if not category:
        return True
    return p.category.lower() == category.lower()


def _matches_price(p: Product, min_price: Optional[float], max_price: Optional[float]) -> bool:
    if min_price is not None and p.price < min_price:
        return False
    if max_price is not None and p.price > max_price:
        return False
    return True


# PUBLIC_INTERFACE
def list_products(query: ProductQuery) -> Tuple[List[Product], int]:
    """
    Returns a filtered and paginated list of products and the total count.
    """
    filtered = [
        p
        for p in _PRODUCTS
        if _matches_query(p, query.q)
        and _matches_category(p, query.category)
        and _matches_price(p, query.min_price, query.max_price)
    ]
    total = len(filtered)
    start = (query.page - 1) * query.page_size
    end = start + query.page_size
    return filtered[start:end], total


# PUBLIC_INTERFACE
def get_product_by_id(product_id: int) -> Optional[Product]:
    """
    Retrieve a single product by its ID, or None if not found.
    """
    for p in _PRODUCTS:
        if p.id == product_id:
            return p
    return None
