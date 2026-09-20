from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User


def notify_user(db: Session, user_id: int, event_type: str, title: str, message: str, *, cpse_id: int | None = None, link: str | None = None) -> Notification:
    notification = Notification(recipient_user_id=user_id, cpse_id=cpse_id, event_type=event_type, title=title, message=message, link=link)
    db.add(notification)
    return notification


def notify_cpse_users(db: Session, cpse_id: int, event_type: str, title: str, message: str, *, link: str | None = None, exclude_user_id: int | None = None) -> int:
    """Create separate inbox entries for approved users of one CPSE."""
    users = db.query(User).filter(User.cpse_id == cpse_id, User.account_status == "APPROVED").all()
    recipients = [user for user in users if user.id != exclude_user_id]
    for user in recipients:
        notify_user(db, user.id, event_type, title, message, cpse_id=cpse_id, link=link)
    return len(recipients)
