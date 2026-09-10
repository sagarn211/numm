from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from app.config.database import Base

class MaterialMapping(Base):
    __tablename__ = "material_mappings"
    __table_args__ = (UniqueConstraint("material_id", name="uq_material_single_national_mapping"),)
    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)
    national_material_id = Column(Integer, ForeignKey("national_materials.id"), nullable=False, index=True)
    mapping_type = Column(String(50), nullable=False, default="MANUAL")
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
