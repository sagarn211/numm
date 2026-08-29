from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.database import Base


class Material(Base):

    __tablename__ = "materials"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    cpse_id = Column(
        Integer,
        ForeignKey("cpses.id"),
        nullable=False
    )

    material_code = Column(
        String(100),
        nullable=False,
        index=True
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

    manufacturer = Column(
        String(200)
    )

    model = Column(
        String(200)
    )

    specifications = Column(
        JSON
    )

    source = Column(
        String(50),
        default="manual"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    cpse = relationship(
        "CPSE",
        back_populates="materials"
    )