import json

from fastapi import APIRouter, Depends, Header, HTTPException, status, Query
from fastapi.responses import StreamingResponse

from ..notification_models import (
    Notification,
    PublishNotificationRequest,
    NotificationListResponse,
    SubscriptionResponse,
)
from ..notification_store import (
    create_notification,
    get_user_notifications,
    get_notification_stats,
    mark_notification_read,
    mark_all_notifications_read,
    create_sse_stream,
)


router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_user_id(x_user_id: str | None = Header(default=None, alias="X-User-Id")) -> str:
    """
    Resolve the user id from the X-User-Id header.
    
    Required for user notification scoping.
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-User-Id header is required",
        )
    return x_user_id


async def format_sse_message(notification: Notification) -> str:
    """Format a notification as an SSE message."""
    data = {
        "id": notification.id,
        "type": notification.type,
        "title": notification.title,
        "message": notification.message,
        "data": notification.data,
        "created_at": notification.created_at.isoformat(),
        "read": notification.read
    }
    return f"data: {json.dumps(data)}\n\n"


# PUBLIC_INTERFACE
@router.post(
    "/subscribe",
    summary="Subscribe to notifications",
    description="Stores per-user SSE channel using X-User-Id header for future notification delivery.",
    response_model=SubscriptionResponse,
    operation_id="subscribe_notifications",
)
async def subscribe_to_notifications(user_id: str = Depends(get_user_id)) -> SubscriptionResponse:
    """
    Subscribe a user to receive notifications. This registers the user for notification delivery.
    The actual SSE stream is established via the /notifications/stream endpoint.
    """
    # This endpoint mainly serves as documentation and confirmation
    # The actual subscription happens when connecting to the SSE stream
    return SubscriptionResponse(
        user_id=user_id,
        message=f"User {user_id} subscribed to notifications. Connect to /notifications/stream for SSE."
    )


# PUBLIC_INTERFACE
@router.get(
    "/stream",
    summary="SSE notification stream",
    description="Server-sent events endpoint emitting real-time notifications for the authenticated user.",
    operation_id="stream_notifications",
    responses={
        200: {
            "description": "SSE stream of notifications",
            "content": {"text/plain": {"schema": {"type": "string"}}},
        }
    },
)
async def stream_notifications(user_id: str = Depends(get_user_id)):
    """
    Establishes an SSE connection for real-time notifications.
    Returns a stream of notifications formatted as Server-Sent Events.
    """
    async def event_generator():
        """Generate SSE events for the user."""
        try:
            # Send connection confirmation
            yield "data: {\"type\": \"connected\", \"message\": \"Connected to notification stream\"}\n\n"
            
            # Stream notifications
            async for notification in create_sse_stream(user_id):
                yield await format_sse_message(notification)
        except Exception as e:
            # Log error and close connection gracefully
            yield f"data: {{\"type\": \"error\", \"message\": \"Connection error: {str(e)}\"}}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        },
    )


# PUBLIC_INTERFACE
@router.post(
    "/publish",
    summary="Publish notification",
    description="Admin/dev-only endpoint to simulate sending notifications with payload types: 'order_update', 'price_drop', or 'new_arrival'.",
    operation_id="publish_notification",
    responses={
        201: {"description": "Notification published successfully"},
    },
    status_code=201,
)
async def publish_notification(request: PublishNotificationRequest) -> dict:
    """
    Publish a notification to one or all users. 
    For development and testing purposes - in production this would have proper authentication.
    """
    try:
        notification_ids = await create_notification(request)
        return {
            "message": "Notification published successfully",
            "notification_ids": notification_ids,
            "target_user": request.user_id or "all_users",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish notification: {str(e)}",
        )


# PUBLIC_INTERFACE
@router.get(
    "",
    summary="List recent notifications",
    description="Returns a paginated list of recent notifications for the authenticated user.",
    response_model=NotificationListResponse,
    operation_id="list_notifications",
)
async def list_notifications(
    user_id: str = Depends(get_user_id),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of notifications to return"),
    include_read: bool = Query(True, description="Whether to include read notifications"),
) -> NotificationListResponse:
    """
    List recent notifications for the user with optional filtering.
    """
    notifications = get_user_notifications(user_id, limit=limit)
    
    if not include_read:
        notifications = [n for n in notifications if not n.read]
    
    total, unread_count = get_notification_stats(user_id)
    
    return NotificationListResponse(
        items=notifications,
        total=len(notifications) if not include_read else total,
        unread_count=unread_count,
    )


# PUBLIC_INTERFACE
@router.patch(
    "/{notification_id}/read",
    summary="Mark notification as read",
    description="Mark a specific notification as read for the authenticated user.",
    status_code=204,
    operation_id="mark_notification_read",
)
async def mark_notification_as_read(
    notification_id: str,
    user_id: str = Depends(get_user_id),
) -> None:
    """
    Mark a specific notification as read.
    """
    success = mark_notification_read(user_id, notification_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or does not belong to user",
        )


# PUBLIC_INTERFACE
@router.post(
    "/mark-all-read",
    summary="Mark all notifications as read",
    description="Mark all notifications as read for the authenticated user.",
    operation_id="mark_all_notifications_read",
)
async def mark_all_as_read(user_id: str = Depends(get_user_id)) -> dict:
    """
    Mark all notifications for the user as read.
    """
    count = mark_all_notifications_read(user_id)
    return {
        "message": f"Marked {count} notifications as read",
        "count": count,
    }


# PUBLIC_INTERFACE
@router.get(
    "/docs/websocket-usage",
    summary="WebSocket usage guide",
    description="Provides information on how to use the notification SSE stream.",
    operation_id="websocket_usage_guide",
)
async def websocket_usage_guide() -> dict:
    """
    Provides usage instructions for the SSE notification stream.
    Note: This is actually Server-Sent Events (SSE), not WebSocket, but provides similar real-time capabilities.
    """
    return {
        "type": "Server-Sent Events (SSE)",
        "endpoint": "/notifications/stream",
        "method": "GET",
        "headers_required": {"X-User-Id": "your-user-id"},
        "description": "Connect to receive real-time notifications as SSE stream",
        "example_curl": "curl -H 'X-User-Id: user123' -H 'Accept: text/event-stream' '/notifications/stream'",
        "event_format": {
            "type": "string - notification type (order_update, price_drop, new_arrival)",
            "title": "string - notification title",
            "message": "string - notification content",
            "data": "object - additional notification data",
            "created_at": "ISO datetime string",
            "read": "boolean - read status"
        }
    }
