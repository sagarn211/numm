from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.sql import func

from app.config.database import Base


class ImportBatch(Base):

    __tablename__ = "import_batches"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    filename = Column(
        String(255),
        nullable=False
    )

    file_type = Column(
        String(20),
        nullable=False
    )

    cpse_id = Column(
        Integer,
        nullable=False
    )

    total_rows = Column(
        Integer,
        default=0
    )

    successful_rows = Column(
        Integer,
        default=0
    )

    failed_rows = Column(
        Integer,
        default=0
    )

    status = Column(
        String(50),
        default="processing"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )