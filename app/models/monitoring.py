from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime, timezone

class Monitoring(Base):
    __tablename__ = "monitoring"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    
    # Transport stats
    no_of_transport = Column(Integer, default=0)
    no_of_mamii_lgas = Column(Integer, default=0)
    by_tricycle_ambulance = Column(Integer, default=0)
    bls = Column(Integer, default=0)
    als = Column(Integer, default=0)
    helicopters = Column(Integer, default=0)
    community_volunteers = Column(Integer, default=0)
    
    # Classification stats
    labor_transportation = Column(Integer, default=0)
    obstetric_transportation = Column(Integer, default=0)
    neonatal_transportation = Column(Integer, default=0)
    
    # Incident Types Stats
    paediatric_over_5 = Column(Integer, default=0)
    drowning = Column(Integer, default=0)
    snake_bite = Column(Integer, default=0)
    other_weapons = Column(Integer, default=0)
    gunshot = Column(Integer, default=0)
    others = Column(Integer, default=0)
    paediatric_under_5 = Column(Integer, default=0)
    neonatal_under_5 = Column(Integer, default=0)
    obstetric_accident = Column(Integer, default=0)
    rta = Column(Integer, default=0)
    
    # Capabilities
    bemonc = Column(Integer, default=0)
    cemonc = Column(Integer, default=0)
    
    # Outcomes
    maternal_mortalities = Column(Integer, default=0)
    neonatal_mortalities = Column(Integer, default=0)
    
    remark = Column(Text, nullable=True)
    
    # Geographic Scope
    state_id = Column(Integer, ForeignKey("states.id"), nullable=True)
    
    # Audit tracking matching production payload
    date_added = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    added_by = Column(String(255), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc), nullable=True)
    updated_by = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    state = relationship("State")
