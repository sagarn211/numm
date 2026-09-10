from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import relationship
from app.config.database import Base

class Material(Base):
    __tablename__ = "materials"
    __table_args__ = (UniqueConstraint("cpse_id", "material_code", name="uq_cpse_material_code"),)

    id = Column(Integer, primary_key=True, index=True)
    cpse_id = Column(Integer, ForeignKey("cpses.id"), nullable=False, index=True)
    import_batch_id = Column(Integer, ForeignKey("import_batches.id"), nullable=True, index=True)

    # Kept for previous frontend compatibility.
    material_code = Column(String(120), nullable=False, index=True)
    description = Column(String(1000), nullable=False)

    original_description = Column(String(1000), nullable=True)
    cleaned_description = Column(String(1000), nullable=True)
    normalized_description = Column(String(1000), nullable=True)
    recommended_standard_description = Column(String(1000), nullable=True)
    approved_standard_description = Column(String(1000), nullable=True)

    category = Column(String(150), nullable=True, index=True)
    subcategory = Column(String(150), nullable=True, index=True)
    classification_confidence = Column(Float, nullable=True)
    classification_source = Column(String(50), nullable=True)
    classification_version = Column(String(50), nullable=True)
    unit = Column(String(50), nullable=True)
    manufacturer = Column(String(255), nullable=True)
    model = Column(String(255), nullable=True)
    specifications = Column(JSON, nullable=True, default=dict)

    source = Column(String(50), nullable=False, default="MANUAL")
    status = Column(String(40), nullable=False, default="ACTIVE")
    matching_status = Column(String(40), nullable=False, default="NOT_PROCESSED")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    cpse = relationship("CPSE", back_populates="materials")
