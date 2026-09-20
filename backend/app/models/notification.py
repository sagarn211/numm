from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.config.database import Base


class Notification(Base):
    """A notification owned by one user; CPSE is retained as event context."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    cpse_id = Column(Integer, ForeignKey("cpses.id"), nullable=True, index=True)
    event_type = Column(String(80), nullable=False)
    title = Column(String(180), nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String(255), nullable=True)
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
