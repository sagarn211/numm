from sqlalchemy import Column, Float, ForeignKey, Integer, String
from app.config.database import Base

class RequestItem(Base):
    __tablename__ = "request_items"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("material_requests.id"), nullable=False, index=True)
    national_material_id = Column(Integer, ForeignKey("national_materials.id"), nullable=False, index=True)
    requested_quantity = Column(Float, nullable=False)
    uom = Column(String(50), nullable=False, default="EA")
