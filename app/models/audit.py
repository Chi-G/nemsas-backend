from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime, timezone

class SystemAuditLog(Base):
    __tablename__ = "system_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(50), index=True)
    record_id = Column(String(100)) # Could be integer ID or UUID represented as string
    action = Column(String(20)) # CREATE, UPDATE, DELETE
    changes = Column(JSON, nullable=True)
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User")
