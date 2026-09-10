from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from app.config.database import Base

class IntegrationSync(Base):
    __tablename__ = "integration_syncs"
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False, default="SAP")
    cpse_id = Column(Integer, ForeignKey("cpses.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    records_received = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    status = Column(String(40), nullable=False, default="RUNNING")
    error_message = Column(Text, nullable=True)
    connector = Column(String(50), nullable=False, default="MOCK")
    correlation_id = Column(String(80), nullable=True, index=True)
    delta_token = Column(String(500), nullable=True)
