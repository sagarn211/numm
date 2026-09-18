from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from app.config.database import Base


class MaterialClusterMember(Base):
    __tablename__ = "material_cluster_members"
    __table_args__ = (UniqueConstraint("cluster_id", "material_id", name="uq_cluster_material_member"),)
    id = Column(Integer, primary_key=True)
    cluster_id = Column(Integer, ForeignKey("material_clusters.id", ondelete="CASCADE"), nullable=False, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)
    member_type = Column(String(30), nullable=False, default="IDENTITY")
    classification = Column(String(40), nullable=True)
    relationship_type = Column(String(40), nullable=True)
    membership_status = Column(String(20), nullable=False, default="ACTIVE")
    ai_match_id = Column(Integer, ForeignKey("material_matches.id"), nullable=True)
    confidence = Column(Float, nullable=True)
    added_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    removed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    removed_at = Column(DateTime, nullable=True)
    removal_reason = Column(Text, nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
