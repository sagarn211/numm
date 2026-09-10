from sqlalchemy import Column, Float, ForeignKey, Integer, String
from app.config.database import Base

class StockAllocation(Base):
    __tablename__ = "stock_allocations"
    id = Column(Integer, primary_key=True, index=True)
    request_item_id = Column(Integer, ForeignKey("request_items.id"), nullable=False, index=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id"), nullable=False, index=True)
    source_cpse_id = Column(Integer, ForeignKey("cpses.id"), nullable=False, index=True)
    allocated_quantity = Column(Float, nullable=False)
    status = Column(String(40), nullable=False, default="PROPOSED")
