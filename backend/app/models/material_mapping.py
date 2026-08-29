from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.sql import func

from app.config.database import Base


class MaterialMapping(Base):

    __tablename__ = "material_mappings"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    material_id = Column(
        Integer,
        ForeignKey("materials.id"),
        nullable=False
    )

    national_material_id = Column(
        Integer,
        ForeignKey("national_materials.id"),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )