from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from app.config.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(40), nullable=False, default="CPSE_OFFICER")
    cpse_id = Column(Integer, ForeignKey("cpses.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
