from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
from app.models.role import Role
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True, default="")
    last_name = Column(String, nullable=False)
    user_name = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    sex = Column(Integer, nullable=True) # 1 for Male, 0 for Female, etc.
    
    street1 = Column(String, nullable=True)
    street2 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True)
    profile_picture = Column(String, nullable=True, default=None)
    is_password_changed = Column(Boolean, default=False, nullable=False)
    date_joined = Column(DateTime(timezone=True), server_default=func.now())

    
    user_type = Column(String, nullable=True) # Role ID or Enum
    real_user_type = Column(String, nullable=True)
    organisation_name = Column(String, nullable=True)
    supervisor_user_id = Column(String, nullable=True) # Could be a FK to self later
    
    emergency_treatment_center_id = Column(Integer, nullable=True)
    etc_id = Column(Integer, nullable=True)
    ambulance_id = Column(Integer, nullable=True)
    
    state_id = Column(Integer, ForeignKey("states.id"), nullable=True)
    lga_id = Column(Integer, ForeignKey("lgas.id"), nullable=True)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=True)

    # Relationships
    state = relationship("State")
    lga = relationship("LGA")
    ward = relationship("Ward")
