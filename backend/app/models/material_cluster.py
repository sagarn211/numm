from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from app.config.database import Base


class MaterialCluster(Base):
    __tablename__ = "material_clusters"
    id = Column(Integer, primary_key=True)
    cluster_code = Column(String(40), nullable=True, unique=True, index=True)
    status = Column(String(30), nullable=False, default="PROPOSED", index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    submitted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejected_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    canonical_material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    national_material_id = Column(Integer, ForeignKey("national_materials.id"), nullable=True)
    risk_level = Column(String(10), nullable=False, default="MEDIUM")
    review_comment = Column(Text, nullable=True)
    approval_comment = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
