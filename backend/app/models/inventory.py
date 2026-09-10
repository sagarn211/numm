from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from app.config.database import Base

class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (UniqueConstraint("material_id", "warehouse", name="uq_inventory_material_warehouse"),)

    id = Column(Integer, primary_key=True, index=True)
    cpse_id = Column(Integer, ForeignKey("cpses.id"), nullable=False, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)
    warehouse = Column(String(255), nullable=False, default="MAIN")
    available_quantity = Column(Float, nullable=False, default=0.0)
    reserved_quantity = Column(Float, nullable=False, default=0.0)
    uom = Column(String(50), nullable=False, default="EA")
    unit_cost = Column(Float, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
