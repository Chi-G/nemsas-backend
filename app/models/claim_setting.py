from sqlalchemy import Column, String, Integer, DateTime, UUID, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime, timezone

class ClaimSetting(Base):
    __tablename__ = "claim_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, index=True, nullable=False)
    value = Column(String(500), nullable=False)
    
    date_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Can track which user made the change
    updated_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    updated_by = relationship("User")
