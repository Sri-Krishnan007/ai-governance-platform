import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Notification, User
from app.schemas import NotificationResponse
from app.auth import get_current_user

logger = logging.getLogger("app.routers.notifications")

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)

@router.get("", response_model=List[NotificationResponse])
def get_user_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve notifications list for the current authenticated user."""
    logger.info(f"User '{current_user.username}' fetching notifications (unread_only={unread_only})")
    
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    
    if unread_only:
        query = query.filter(Notification.read == False)
        
    notifications = query.order_by(Notification.created_at.desc()).all()
    return notifications

@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a specific notification as read."""
    logger.info(f"User '{current_user.username}' marking notification ID {notification_id} as read")
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
        
    notification.read = True
    
    try:
        db.commit()
        db.refresh(notification)
        return notification
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to mark notification ID {notification_id} as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification"
        )

@router.post("/read-all")
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all unread notifications for the user as read."""
    logger.info(f"User '{current_user.username}' marking all notifications as read")
    
    try:
        db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.read == False
        ).update({"read": True}, synchronize_session=False)
        
        db.commit()
        return {"detail": "All notifications marked as read successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to mark all notifications as read for user {current_user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notifications"
        )
