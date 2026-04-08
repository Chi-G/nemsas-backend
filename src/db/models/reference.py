from sqlalchemy import String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base
from typing import List, Optional

class State(Base):
    __tablename__ = "states"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    population: Mapped[int] = mapped_column(Integer, default=0)
    
    lgas: Mapped[List["LGA"]] = relationship(back_populates="state")

class LGA(Base):
    __tablename__ = "lgas"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    state_id: Mapped[int] = mapped_column(ForeignKey("states.id"))
    name: Mapped[str] = mapped_column(String(100), index=True)
    
    state: Mapped[State] = relationship(back_populates="lgas")

class Drug(Base):
    __tablename__ = "drugs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    dosage_form: Mapped[Optional[str]] = mapped_column(String(100))
    is_nhia_approved: Mapped[bool] = mapped_column(default=True)
    is_active: Mapped[bool] = mapped_column(default=True)
