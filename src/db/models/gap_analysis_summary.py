from sqlalchemy import String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base
from datetime import datetime, timezone
from typing import Optional

class GapAnalysisSummary(Base):
    """
    Stores nightly aggregated gap analysis data for States and LGAs.
    Sourced from NPC population data and current ambulance inventory.
    """
    __tablename__ = "gap_analysis_summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Hierarchy - State or LGA
    state_id: Mapped[int] = mapped_column(ForeignKey("states.id"), index=True)
    lga_id: Mapped[Optional[int]] = mapped_column(ForeignKey("lgas.id"), index=True, nullable=True) # Null if state-level summary
    
    region_name: Mapped[str] = mapped_column(String(100))
    region_type: Mapped[str] = mapped_column(String(20)) # 'state' or 'lga'
    
    # Population & Target
    population: Mapped[int] = mapped_column(Integer, default=0)
    target_ambulances: Mapped[int] = mapped_column(Integer, default=0)
    
    # Ambulance Breakdown
    total_active: Mapped[int] = mapped_column(Integer, default=0)
    total_on_duty: Mapped[int] = mapped_column(Integer, default=0)
    total_under_maintenance: Mapped[int] = mapped_column(Integer, default=0)
    total_pending_verification: Mapped[int] = mapped_column(Integer, default=0)
    total_pledged: Mapped[int] = mapped_column(Integer, default=0)
    
    # Gap Metrics
    gap_count: Mapped[int] = mapped_column(Integer, default=0)
    coverage_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    color_band: Mapped[str] = mapped_column(String(50)) # critically underserved, underserved, etc.
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
