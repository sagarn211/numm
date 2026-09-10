from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from app.config.database import Base

class MaterialRequest(Base):
    __tablename__ = "material_requests"
    id = Column(Integer, primary_key=True, index=True)
    request_number = Column(String(80), unique=True, nullable=True, index=True)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    requesting_cpse_id = Column(Integer, ForeignKey("cpses.id"), nullable=False)
    status = Column(String(40), nullable=False, default="DRAFT")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
