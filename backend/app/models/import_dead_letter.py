from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.config.database import Base


class ImportDeadLetter(Base):
    __tablename__ = "import_dead_letters"

    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey("import_batches.id"), nullable=False, index=True)
    task_id = Column(String(255), nullable=True)
    attempts = Column(Integer, nullable=False)
    error_message = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
