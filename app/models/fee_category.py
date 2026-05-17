from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base
from sqlalchemy.sql import func

class FeeCategory(Base):
    __tablename__ = "fee_categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    code = Column(String, nullable=True, default="")
    description = Column(String, nullable=True)
    is_medicine = Column(Boolean, default=False)
    date_added = Column(DateTime(timezone=True), server_default=func.now())

    services = relationship("Service", back_populates="fee_category", cascade="all, delete-orphan")

