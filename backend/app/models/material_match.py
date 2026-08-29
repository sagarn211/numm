from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.sql import func

from app.config.database import Base


class MaterialMatch(Base):

    __tablename__ = "material_matches"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    material_a_id = Column(
        Integer,
        ForeignKey("materials.id"),
        nullable=False
    )

    material_b_id = Column(
        Integer,
        ForeignKey("materials.id"),
        nullable=False
    )

    semantic_score = Column(
        Float,
        default=0
    )

    attribute_score = Column(
        Float,
        default=0
    )

    final_score = Column(
        Float,
        default=0
    )

    classification = Column(
        String(50)
    )

    status = Column(
        String(50),
        default="pending"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )