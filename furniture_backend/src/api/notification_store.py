import uuid
import asyncio
from typing import Dict, List, Set, AsyncGenerator
from datetime import datetime, timedelta
from collections import deque

from .notification_models import Notification, PublishNotificationRequest


# In-memory storage for notifications and subscriptions
# In production, this would be replaced with Redis or a database
_NOTIFICATIONS: Dict[str, deque] = {}  # user_id -> deque of notifications
_SUBSCRIPTIONS: Dict[str, Set[asyncio.Queue]] = {}  # user_id -> set of SSE queues
_MAX_NOTIFICATIONS_PER_USER = 100  # Limit notifications per user
_NOTIFICATION_TTL_HOURS = 24  # Auto-prune notifications older than 24 hours


def _get_user_notifications(user_id: str) -> deque:
    """Get or create notifications deque for a user."""
    if user_id not in _NOTIFICATIONS:
        _NOTIFICATIONS[user_id] = deque(maxlen=_MAX_NOTIFICATIONS_PER_USER)
    return _NOTIFICATIONS[user_id]


def _get_user_subscriptions(user_id: str) -> Set[asyncio.Queue]:
    """Get or create subscription set for a user."""
    if user_id not in _SUBSCRIPTIONS:
        _SUBSCRIPTIONS[user_id] = set()
    return _SUBSCRIPTIONS[user_id]


def _prune_old_notifications():
    """Remove notifications older than TTL."""
    cutoff = datetime.now() - timedelta(hours=_NOTIFICATION_TTL_HOURS)
    for user_id, notifications in _NOTIFICATIONS.items():
        # Convert deque to list, filter, and recreate deque
        filtered = [n for n in notifications if n.created_at > cutoff]
        _NOTIFICATIONS[user_id] = deque(filtered, maxlen=_MAX_NOTIFICATIONS_PER_USER)


# PUBLIC_INTERFACE
def add_subscription(user_id: str, queue: asyncio.Queue) -> None:
    """Add an SSE subscription queue for a user."""
    subscriptions = _get_user_subscriptions(user_id)
    subscriptions.add(queue)


# PUBLIC_INTERFACE
def remove_subscription(user_id: str, queue: asyncio.Queue) -> None:
    """Remove an SSE subscription queue for a user."""
    if user_id in _SUBSCRIPTIONS:
        _SUBSCRIPTIONS[user_id].discard(queue)
        # Clean up empty subscription sets
        if not _SUBSCRIPTIONS[user_id]:
            del _SUBSCRIPTIONS[user_id]


# PUBLIC_INTERFACE
async def create_notification(request: PublishNotificationRequest) -> List[str]:
    """Create and publish a notification. Returns list of notification IDs created."""
    notification_id = str(uuid.uuid4())
    created_at = datetime.now()
    
    # Determine target users
    target_users = []
    if request.user_id:
        target_users = [request.user_id]
    else:
        # Broadcast to all users with subscriptions
        target_users = list(_SUBSCRIPTIONS.keys())
    
    created_notifications = []
    
    for user_id in target_users:
        # Create notification for this user
        notification = Notification(
            id=f"{notification_id}_{user_id}",
            user_id=user_id,
            type=request.type,
            title=request.title,
            message=request.message,
            data=request.data,
            created_at=created_at,
            read=False
        )
        
        # Store notification
        user_notifications = _get_user_notifications(user_id)
        user_notifications.appendleft(notification)  # Latest first
        
        # Send to SSE subscribers
        user_subscriptions = _get_user_subscriptions(user_id)
        for queue in list(user_subscriptions):  # Copy to avoid modification during iteration
            try:
                await queue.put(notification)
            except asyncio.QueueFull:
                # Remove dead subscription
                user_subscriptions.discard(queue)
        
        created_notifications.append(notification.id)
    
    # Prune old notifications
    _prune_old_notifications()
    
    return created_notifications


# PUBLIC_INTERFACE
def get_user_notifications(user_id: str, limit: int = 50) -> List[Notification]:
    """Get recent notifications for a user."""
    user_notifications = _get_user_notifications(user_id)
    # Return up to limit notifications, newest first
    return list(user_notifications)[:limit]


# PUBLIC_INTERFACE
def get_notification_stats(user_id: str) -> tuple[int, int]:
    """Get total and unread notification counts for a user."""
    notifications = get_user_notifications(user_id)
    total = len(notifications)
    unread = sum(1 for n in notifications if not n.read)
    return total, unread


# PUBLIC_INTERFACE
def mark_notification_read(user_id: str, notification_id: str) -> bool:
    """Mark a specific notification as read. Returns True if found and updated."""
    user_notifications = _get_user_notifications(user_id)
    for notification in user_notifications:
        if notification.id == notification_id and notification.user_id == user_id:
            notification.read = True
            return True
    return False


# PUBLIC_INTERFACE
def mark_all_notifications_read(user_id: str) -> int:
    """Mark all notifications for a user as read. Returns count of notifications marked."""
    user_notifications = _get_user_notifications(user_id)
    count = 0
    for notification in user_notifications:
        if not notification.read:
            notification.read = True
            count += 1
    return count


# PUBLIC_INTERFACE
async def create_sse_stream(user_id: str) -> AsyncGenerator[Notification, None]:
    """Create an SSE stream for a user's notifications."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    add_subscription(user_id, queue)
    
    try:
        while True:
            try:
                # Wait for notification with timeout to allow cleanup
                notification = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield notification
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                continue
    finally:
        remove_subscription(user_id, queue)
