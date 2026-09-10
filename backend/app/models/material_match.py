from datetime import datetime
from sqlalchemy import CheckConstraint, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from app.config.database import Base

class MaterialMatch(Base):
    __tablename__ = "material_matches"
    __table_args__ = (
        CheckConstraint("material_a_id < material_b_id", name="ck_material_match_ordered_pair"),
        UniqueConstraint("material_a_id", "material_b_id", name="uq_material_match_pair"),
    )
    id = Column(Integer, primary_key=True, index=True)
    material_a_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)
    material_b_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)

    semantic_score = Column(Float, nullable=True)
    attribute_score = Column(Float, nullable=True)
    fuzzy_score = Column(Float, nullable=True)
    final_score = Column(Float, nullable=False)
    classification = Column(String(50), nullable=False)

    attributes_a = Column(JSON, nullable=True)
    attributes_b = Column(JSON, nullable=True)
    explanation = Column(Text, nullable=True)
    model_name = Column(String(255), nullable=True)
    matcher_version = Column(String(80), nullable=True)

    status = Column(String(40), nullable=False, default="PENDING")
    submitted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
