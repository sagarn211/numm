from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.sql import func

from app.config.database import Base


class NationalMaterial(Base):

    __tablename__ = "national_materials"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    national_code = Column(
        String(100),
        unique=True,
        nullable=False
    )

    description = Column(
        Text,
        nullable=False
    )

    category = Column(
        String(150)
    )

    unit = Column(
        String(50)
    )

    specifications = Column(
        Text
    )

    status = Column(
        String(50),
        default="active"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )