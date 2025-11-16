"""
API routes for Notification Service
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import logging

from app.database import get_db
from app.models import Notification
from app.schemas import NotificationCreate, NotificationResponse, MessageResponse
from app.dependencies import get_current_user
from app.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


async def simulate_email(notification: Notification):
    """Simulate sending email"""
    logger.info(
        f"📧 SIMULATED EMAIL:\n"
        f"To: User {notification.user_id}\n"
        f"Subject: {notification.title}\n"
        f"Body: {notification.content}\n"
        f"Type: {notification.notification_type}"
    )
    # In production, replace with actual email sending logic
    # using SMTP or services like SendGrid, AWS SES, etc.


@router.post("/notifications/send", response_model=NotificationResponse, status_code=201)
async def send_notification(
    notification: NotificationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Send notification (called by other services)
    
    This endpoint does NOT require authentication because it's called
    by other internal services (Task Service, etc.)
    """
    
    # Create notification
    new_notif = Notification(
        user_id=notification.user_id,
        notification_type=notification.notification_type,
        title=notification.title,
        content=notification.content
    )
    
    db.add(new_notif)
    await db.commit()
    await db.refresh(new_notif)
    
    # Simulate sending email
    await simulate_email(new_notif)
    
    logger.info(f"Notification sent: {new_notif.id}")
    
    return new_notif.to_dict()


@router.get("/notifications", response_model=list[NotificationResponse])
async def list_notifications(
    is_read: bool = None,
    notification_type: str = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's notifications"""
    
    query = select(Notification).where(Notification.user_id == current_user["user_id"])
    
    if is_read is not None:
        query = query.where(Notification.is_read == is_read)
    
    if notification_type:
        query = query.where(Notification.notification_type == notification_type)
    
    query = query.limit(limit).offset(offset).order_by(Notification.sent_at.desc())
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    return [notif.to_dict() for notif in notifications]


@router.get("/notifications/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get notification details"""
    
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )
    
    # Check ownership
    if str(notification.user_id) != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this notification"
        )
    
    return notification.to_dict()


@router.patch("/notifications/{notification_id}/read", response_model=MessageResponse)
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark notification as read"""
    
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user["user_id"]
        )
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )
    
    notification.is_read = True
    await db.commit()
    
    logger.info(f"Notification marked as read: {notification_id}")
    
    return MessageResponse(
        message="Notification marked as read",
        success=True
    )


@router.patch("/notifications/read-all", response_model=MessageResponse)
async def mark_all_read(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark all user notifications as read"""
    
    await db.execute(
        update(Notification)
        .where(
            Notification.user_id == current_user["user_id"],
            Notification.is_read == False
        )
        .values(is_read=True)
    )
    await db.commit()
    
    logger.info(f"All notifications marked as read for user: {current_user['user_id']}")
    
    return MessageResponse(
        message="All notifications marked as read",
        success=True
    )


@router.get("/notifications/unread/count")
async def get_unread_count(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get count of unread notifications"""
    
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == current_user["user_id"],
            Notification.is_read == False
        )
    )
    notifications = result.scalars().all()
    count = len(notifications)
    
    return {
        "unread_count": count,
        "user_id": current_user["user_id"]
    }
