from fastapi import APIRouter

router = APIRouter(prefix="", tags=["health"])


# PUBLIC_INTERFACE
@router.get(
    "/health",
    summary="Health Check",
    description="Returns service status for monitoring and diagnostics.",
    operation_id="health_check",
    responses={
        200: {
            "description": "Healthy response",
            "content": {"application/json": {}},
        }
    },
)
def health_check():
    """Health check endpoint to verify service is running."""
    return {"status": "ok"}
