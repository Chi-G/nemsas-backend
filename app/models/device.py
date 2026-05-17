from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import uuid

class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    ambulance_id = Column(Integer, nullable=True) # Linked ambulance if any
    
    push_token = Column(String, unique=True, index=True, nullable=False)
    platform = Column(String, nullable=False) # 'ios', 'android'
    device_name = Column(String, nullable=True)
    device_id = Column(String, nullable=True) # Unique per device (hardware ID)
    
    last_active = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", backref="devices")
