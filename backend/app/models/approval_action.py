from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from app.config.database import Base

class ApprovalAction(Base):
    __tablename__ = "approval_actions"
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("material_matches.id"), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)
    comment = Column(Text, nullable=True)
    previous_status = Column(String(40), nullable=True)
    new_status = Column(String(40), nullable=False)
    details = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
