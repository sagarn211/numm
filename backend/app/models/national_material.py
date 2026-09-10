from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, JSON, String
from app.config.database import Base

class NationalMaterial(Base):
    __tablename__ = "national_materials"
    id = Column(Integer, primary_key=True, index=True)
    national_code = Column(String(100), unique=True, nullable=True, index=True)

    # Names preserved for previous frontend.
    description = Column(String(1000), nullable=False)
    category = Column(String(150), nullable=True)
    subcategory = Column(String(150), nullable=True)
    unit = Column(String(50), nullable=True)
    specifications = Column(JSON, nullable=True, default=dict)
    provenance = Column(JSON, nullable=True, default=dict)
    code_scheme_version = Column(String(20), nullable=False, default="2")

    status = Column(String(40), nullable=False, default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
