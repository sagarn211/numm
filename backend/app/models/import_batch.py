from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from app.config.database import Base

class ImportBatch(Base):
    __tablename__ = "import_batches"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_path = Column(String(1000), nullable=True)
    import_type = Column(String(30), nullable=False, default="MATERIAL")
    conflict_policy = Column(String(30), nullable=False, default="REJECT")
    cpse_id = Column(Integer, ForeignKey("cpses.id"), nullable=False)
    total_rows = Column(Integer, default=0)
    successful_rows = Column(Integer, default=0)
    failed_rows = Column(Integer, default=0)
    warning_rows = Column(Integer, default=0)
    status = Column(String(50), nullable=False, default="PREVIEW_READY")
    idempotency_key = Column(String(120), nullable=True, unique=True, index=True)
    processed_rows = Column(Integer, default=0)
    progress_percent = Column(Integer, default=0)
    current_stage = Column(String(50), nullable=True)
    cancellation_requested = Column(Boolean, default=False, nullable=False)
    error_message = Column(String(1000), nullable=True)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    confirmed_at = Column(DateTime, nullable=True)
