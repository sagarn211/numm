from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, UniqueConstraint

from app.config.database import Base


class TaxonomyCode(Base):
    __tablename__ = "material_taxonomy_codes"
    __table_args__ = (
        UniqueConstraint("level", "name", name="uq_taxonomy_level_name"),
        UniqueConstraint("level", "code", name="uq_taxonomy_level_code"),
    )

    id = Column(Integer, primary_key=True)
    level = Column(String(20), nullable=False)
    name = Column(String(150), nullable=False)
    code = Column(String(3), nullable=False)
    parent_name = Column(String(150), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
