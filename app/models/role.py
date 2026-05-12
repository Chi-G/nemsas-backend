from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.db.session import Base

class Role(Base):
    __tablename__ = "roles"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)

    # You might want to link this to users later
    # users = relationship("User", back_populates="role")
