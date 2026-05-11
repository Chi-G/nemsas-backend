from sqlalchemy import Column, String, Integer, Boolean, DateTime
from app.db.session import Base
from datetime import datetime, timezone

class Drug(Base):
    __tablename__ = "drugs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)
    dosage_form = Column(String(100), nullable=True)
    is_nhia_approved = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
