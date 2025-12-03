from typing import List, Literal, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime


# PUBLIC_INTERFACE
class Notification(BaseModel):
    """Represents a notification for a user."""
    id: str = Field(..., description="Unique identifier for the notification")
    user_id: str = Field(..., description="Target user ID")
    type: Literal['order_update', 'price_drop', 'new_arrival'] = Field(..., description="Type of notification")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message content")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional notification data")
    created_at: datetime = Field(..., description="When the notification was created")
    read: bool = Field(False, description="Whether the notification has been read")


# PUBLIC_INTERFACE
class PublishNotificationRequest(BaseModel):
    """Request model for publishing notifications to users."""
    user_id: Optional[str] = Field(None, description="Target user ID (if None, broadcast to all)")
    type: Literal['order_update', 'price_drop', 'new_arrival'] = Field(..., description="Type of notification")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message content")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional notification data")


# PUBLIC_INTERFACE
class NotificationListResponse(BaseModel):
    """Response model for listing user notifications."""
    items: List[Notification] = Field(..., description="List of notifications for the user")
    total: int = Field(..., ge=0, description="Total number of notifications")
    unread_count: int = Field(..., ge=0, description="Number of unread notifications")


# PUBLIC_INTERFACE
class SubscriptionResponse(BaseModel):
    """Response model for subscription status."""
    user_id: str = Field(..., description="User ID that was subscribed")
    message: str = Field(..., description="Confirmation message")
