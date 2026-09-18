from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.config.database import Base


class MaterialImage(Base):
    """CDN-backed visual reference. Image bytes are never stored in PostgreSQL."""
    __tablename__ = "material_images"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id", ondelete="CASCADE"), nullable=False, index=True)
    national_material_id = Column(Integer, ForeignKey("national_materials.id"), nullable=True, index=True)
    image_url = Column(String(2048), nullable=False)
    imagekit_file_id = Column(String(255), nullable=True, unique=True)
    image_type = Column(String(30), nullable=False, default="OTHER")
    source_type = Column(String(40), nullable=False, default="WAREHOUSE_UPLOAD")
    verification_status = Column(String(20), nullable=False, default="PENDING", index=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    source_url = Column(String(2048), nullable=True)
    checksum = Column(String(128), nullable=True, index=True)
    original_filename = Column(String(512), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    material = relationship("Material", back_populates="images")
