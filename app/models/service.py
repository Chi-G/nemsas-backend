from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base
from sqlalchemy.sql import func

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    code = Column(String, nullable=True, default="")
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    fee_category_id = Column(Integer, ForeignKey("fee_categories.id"), nullable=True)
    date_added = Column(DateTime(timezone=True), server_default=func.now())

    fee_category = relationship("FeeCategory", back_populates="services")
