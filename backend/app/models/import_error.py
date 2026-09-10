from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from app.config.database import Base

class ImportRowError(Base):
    __tablename__ = "import_errors"
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("import_batches.id"), nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    field_name = Column(String(120), nullable=True)
    raw_value = Column(Text, nullable=True)
    error_code = Column(String(120), nullable=False)
    error_message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, default="ERROR")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
