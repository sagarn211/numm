from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


def notification_data(notification: Notification) -> dict:
    return {"id": notification.id, "event_type": notification.event_type, "title": notification.title, "message": notification.message, "link": notification.link, "cpse_id": notification.cpse_id, "is_read": notification.is_read, "created_at": notification.created_at}


@router.get("")
def list_notifications(limit: int = 25, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.query(Notification).filter(Notification.recipient_user_id == current_user.id).order_by(Notification.created_at.desc(), Notification.id.desc()).limit(max(1, min(limit, 100))).all()
    return [notification_data(row) for row in rows]


@router.get("/unread-count")
def unread_count(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {"count": db.query(Notification).filter(Notification.recipient_user_id == current_user.id, Notification.is_read.is_(False)).count()}


@router.patch("/{notification_id}/read")
def mark_read(notification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notification = db.get(Notification, notification_id)
    if not notification or notification.recipient_user_id != current_user.id:
        raise HTTPException(404, "Notification not found")
    notification.is_read = True
    db.commit(); db.refresh(notification)
    return notification_data(notification)


@router.post("/mark-all-read")
def mark_all_read(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(Notification).filter(Notification.recipient_user_id == current_user.id, Notification.is_read.is_(False)).update({Notification.is_read: True}, synchronize_session=False)
    db.commit()
    return {"message": "Notifications marked as read"}
