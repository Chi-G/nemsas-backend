from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime, timezone

class PartnerUser(Base):
    __tablename__ = "partner_users"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True, default="")
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True)
    organisation_name = Column(String(255), nullable=True)
    user_type = Column(String(50), default="organization") # e.g. "organization", "admin"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class PartnerPledge(Base):
    __tablename__ = "partner_pledges"
    
    id = Column(Integer, primary_key=True)
    pledge_id_str = Column(String(50), unique=True, index=True) # e.g. "PLG-00031"
    contact_details = Column(String(255), nullable=True)
    donor_name = Column(String(255), nullable=True)
    pledge_type = Column(String(100), nullable=True) # "donation", "investment"
    number_of_ambulance = Column(Integer, default=0)
    
    ambulance_type_id = Column(Integer, ForeignKey("ambulance_types.id"), nullable=True)
    state_id = Column(Integer, ForeignKey("states.id"), nullable=True)
    lga_id = Column(Integer, ForeignKey("lgas.id"), nullable=True)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=True)
    facility_id = Column(Integer, ForeignKey("hospitals.id"), nullable=True)
    
    pledge_date = Column(DateTime(timezone=True), nullable=True)
    delivery_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="pending") # "fulfilled", "pending", "not_fulfilled"
    date_added = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    added_by_id = Column(Integer, ForeignKey("partner_users.id"), nullable=False)
    
    added_by = relationship("PartnerUser")
    ambulance_type = relationship("AmbulanceType")
    state = relationship("State")
    lga = relationship("LGA")
    ward = relationship("Ward")
    facility = relationship("Hospital")

class PartnerFacility(Base):
    __tablename__ = "partner_facilities"
    
    id = Column(Integer, primary_key=True)
    facility_id_str = Column(String(50), unique=True, index=True) # e.g. "Fac-00027"
    facility_name = Column(String(255), nullable=True)
    facility_type = Column(String(100), nullable=True) # "PHC", "SHC"
    facility_location = Column(String(100), nullable=True) # "urban", "rural"
    ownership_type = Column(String(100), nullable=True) # "private", "public"
    communication_devices = Column(String(255), nullable=True) # comma separated
    number_of_ambulance = Column(Integer, default=0)
    address = Column(String(500), nullable=True)
    contact_information = Column(String(255), nullable=True)
    
    state_id = Column(Integer, ForeignKey("states.id"), nullable=True)
    lga_id = Column(Integer, ForeignKey("lgas.id"), nullable=True)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=True)
    
    status = Column(String(50), default="pending") # "approved", "pending"
    date_added = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    added_by_id = Column(Integer, ForeignKey("partner_users.id"), nullable=False)
    
    added_by = relationship("PartnerUser")
    state = relationship("State")
    lga = relationship("LGA")
    ward = relationship("Ward")

class PartnerAmbulance(Base):
    __tablename__ = "partner_ambulances"
    
    id = Column(Integer, primary_key=True)
    ambulance_id_str = Column(String(50), unique=True, index=True) # e.g. "Amb 32"
    
    # Basic Information
    plate_number = Column(String(50), nullable=True)
    make = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)
    accreditation_type = Column(String(50), nullable=True) # BLS, ALS, Keke
    
    state_id = Column(Integer, ForeignKey("states.id"), nullable=True)
    lga_id = Column(Integer, ForeignKey("lgas.id"), nullable=True)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=True)
    facility_id = Column(Integer, ForeignKey("hospitals.id"), nullable=True) # Primary health care facility
    
    vehicle_ownership_type = Column(String(50), nullable=True) # public, private
    driver_name = Column(String(255), nullable=True)
    contact_number = Column(String(50), nullable=True)
    
    # Technical Specification
    fuel_type = Column(String(100), nullable=True)
    other_fuel_type_option = Column(String(100), nullable=True)
    fuel_capacity = Column(String(50), nullable=True)
    communication_devices = Column(String(255), nullable=True) # comma separated
    other_communication_device_option = Column(String(100), nullable=True)
    latitude = Column(String(50), nullable=True)
    longitude = Column(String(50), nullable=True)
    
    # Equipment Inventory
    equipments = Column(String(500), nullable=True) # comma separated
    
    # Compliance and Documentation
    road_worthiness_assessment_date = Column(DateTime(timezone=True), nullable=True)
    road_worthiness_status = Column(String(50), nullable=True)
    last_inspection_date = Column(DateTime(timezone=True), nullable=True)
    next_scheduled_maintenance = Column(DateTime(timezone=True), nullable=True)
    inspection_notes = Column(String(500), nullable=True)
    insurance_provider = Column(String(255), nullable=True)
    insurance_expiration_date = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(String(50), default="active") # active, inactive
    is_out_for_maintenance = Column(Boolean, default=False)
    is_out_of_service = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    added_by_id = Column(Integer, ForeignKey("partner_users.id"), nullable=False)
    
    added_by = relationship("PartnerUser")
    state = relationship("State")
    lga = relationship("LGA")
    ward = relationship("Ward")
    facility = relationship("Hospital")
