from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from app.config.database import Base


class ProcurementRecord(Base):
    __tablename__ = "procurement_records"
    __table_args__ = (UniqueConstraint("cpse_id", "order_number", "line_number", name="uq_procurement_line"),)
    id = Column(Integer, primary_key=True)
    cpse_id = Column(Integer, ForeignKey("cpses.id"), nullable=False, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)
    order_number = Column(String(100), nullable=False)
    line_number = Column(String(30), nullable=False)
    supplier = Column(String(255), nullable=False)
    period = Column(String(7), nullable=False)
    quantity = Column(Float, nullable=False)
    uom = Column(String(50), nullable=False)
    unit_price = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)
    lead_time_days = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
