from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from app.config.database import Base

class DemandRecord(Base):
    __tablename__ = "demand_records"
    id = Column(Integer, primary_key=True, index=True)
    cpse_id = Column(Integer, ForeignKey("cpses.id"), nullable=False, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)
    period = Column(String(40), nullable=False)
    required_quantity = Column(Float, nullable=False)
    uom = Column(String(50), nullable=False, default="EA")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
