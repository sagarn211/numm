from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.database import Base


class CPSE(Base):

    __tablename__ = "cpses"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(200),
        nullable=False
    )

    code = Column(
        String(50),
        unique=True,
        nullable=False
    )

    sector = Column(
        String(100)
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    materials = relationship(
        "Material",
        back_populates="cpse"
    )