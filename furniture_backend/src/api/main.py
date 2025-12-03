from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from .routers import health, products, wishlist
from .routers import cart

# Create FastAPI app with metadata for OpenAPI
app = FastAPI(
    title="Furniture Shop API",
    description="Backend API for a simple furniture shopping app. Provides product catalog endpoints.",
    version="0.1.0",
    openapi_tags=[
        {"name": "health", "description": "Service health and diagnostics"},
        {"name": "products", "description": "Furniture product catalog operations"},
        {"name": "wishlist", "description": "Per-user wishlist operations (scoped via X-User-Id header)"},
        {"name": "cart", "description": "Per-user cart operations (cart is ephemeral, X-User-Id scoped)"}
    ],
)

# Configure CORS - allow frontend on port 3000 and local devs
allowed_origins: List[str] = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*",  # Keep permissive for initial development; tighten later for production.
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  # All headers including X-User-Id allowed
)

# Include routers
app.include_router(health.router)
app.include_router(products.router)
app.include_router(wishlist.router)
app.include_router(cart.router)


def custom_openapi():
    """
    Build a customized OpenAPI schema with app metadata and tags.
    """
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Bind custom OpenAPI generator
app.openapi = custom_openapi  # type: ignore[assignment]
