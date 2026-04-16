from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, delete
from src.db.models.reference import State, LGA
from src.db.models.ambulance import Ambulance, AmbulanceStatus
from src.db.models.partner import Pledge, PledgeStatus
from src.db.models.gap_analysis_summary import GapAnalysisSummary
from typing import List, Dict, Any
import math

class GapAnalysisService:
    @staticmethod
    def get_color_band(coverage_percentage: float) -> str:
        """
        Logic per AC 194:
        below 25% = critically underserved
        25–50% = underserved
        50–75% = partially served
        75%+ = adequately served
        """
        if coverage_percentage < 25:
            return "critically underserved"
        elif coverage_percentage < 50:
            return "underserved"
        elif coverage_percentage < 75:
            return "partially served"
        else:
            return "adequately served"

    @staticmethod
    async def sync_gap_analysis_data(db: AsyncSession):
        """
        Aggregates data for all States and LGAs and populates the GapAnalysisSummary table.
        Satisfies AC 197 (nightly update logic).
        """
        # Clear existing summaries
        await db.execute(delete(GapAnalysisSummary))
        
        # Helper to get valid pledges (AC 191/192)
        async def get_pledged_count(state_id: int, lga_id: int = None):
            query = select(func.sum(Pledge.ambulance_count)).where(
                and_(
                    Pledge.status.in_([PledgeStatus.PENDING, PledgeStatus.IN_PROGRESS, PledgeStatus.PARTIALLY_FULFILLED]),
                    Pledge.target_state_id == state_id
                )
            )
            if lga_id:
                query = query.where(Pledge.target_lga_id == lga_id)
            result = await db.execute(query)
            return result.scalar() or 0

        # Process States
        result = await db.execute(select(State))
        states = result.scalars().all()
        
        for state in states:
            # Aggregate ambulances in state
            result = await db.execute(select(Ambulance).where(Ambulance.state_id == state.id))
            ambulances = result.scalars().all()
            
            counts = {
                "active": sum(1 for a in ambulances if a.status in [AmbulanceStatus.ACTIVE, AmbulanceStatus.ON_DUTY]),
                "pending_verification": sum(1 for a in ambulances if a.status == AmbulanceStatus.PENDING_VERIFICATION),
                "under_maintenance": sum(1 for a in ambulances if a.status == AmbulanceStatus.UNDER_MAINTENANCE),
                "pledged": await get_pledged_count(state.id)
            }
            
            target = math.ceil(state.population / 50000)
            gap = max(0, target - counts["active"])
            coverage = (counts["active"] / target * 100) if target > 0 else 0.0
            
            summary = GapAnalysisSummary(
                state_id=state.id,
                region_name=state.name,
                region_type="state",
                population=state.population,
                target_ambulances=target,
                total_active=counts["active"],
                total_pending_verification=counts["pending_verification"],
                total_under_maintenance=counts["under_maintenance"],
                total_pledged=counts["pledged"],
                gap_count=gap,
                coverage_percentage=coverage,
                color_band=GapAnalysisService.get_color_band(coverage)
            )
            db.add(summary)
            
            # Process LGAs in state (AC 193)
            result = await db.execute(select(LGA).where(LGA.state_id == state.id))
            lgas = result.scalars().all()
            
            for lga in lgas:
                lga_ambulances = [a for a in ambulances if a.lga_id == lga.id]
                
                lga_counts = {
                    "active": sum(1 for a in lga_ambulances if a.status in [AmbulanceStatus.ACTIVE, AmbulanceStatus.ON_DUTY]),
                    "pending_verification": sum(1 for a in lga_ambulances if a.status == AmbulanceStatus.PENDING_VERIFICATION),
                    "under_maintenance": sum(1 for a in lga_ambulances if a.status == AmbulanceStatus.UNDER_MAINTENANCE),
                    "pledged": await get_pledged_count(state.id, lga.id)
                }
                
                lga_target = math.ceil(lga.population / 50000)
                lga_gap = max(0, lga_target - lga_counts["active"])
                lga_coverage = (lga_counts["active"] / lga_target * 100) if lga_target > 0 else 0.0
                
                lga_summary = GapAnalysisSummary(
                    state_id=state.id,
                    lga_id=lga.id,
                    region_name=lga.name,
                    region_type="lga",
                    population=lga.population,
                    target_ambulances=lga_target,
                    total_active=lga_counts["active"],
                    total_pending_verification=lga_counts["pending_verification"],
                    total_under_maintenance=lga_counts["under_maintenance"],
                    total_pledged=lga_counts["pledged"],
                    gap_count=lga_gap,
                    coverage_percentage=lga_coverage,
                    color_band=GapAnalysisService.get_color_band(lga_coverage)
                )
                db.add(lga_summary)
        
        await db.commit()

    @staticmethod
    async def get_national_summary(db: AsyncSession) -> Dict[str, Any]:
        """AC 191: national summary endpoint"""
        result = await db.execute(select(func.sum(State.population)))
        total_pop = result.scalar() or 0
        target = math.ceil(total_pop / 50000)
        
        result = await db.execute(select(GapAnalysisSummary).filter(GapAnalysisSummary.region_type == "state"))
        active_states = result.scalars().all()
        
        return {
            "national_target": target,
            "total_active": sum(s.total_active for s in active_states),
            "total_pledged": sum(s.total_pledged for s in active_states),
            "total_gap": sum(s.gap_count for s in active_states)
        }

    @staticmethod
    async def get_state_summaries(db: AsyncSession) -> List[GapAnalysisSummary]:
        """AC 192 & 198: optimized state summaries"""
        result = await db.execute(select(GapAnalysisSummary).filter(GapAnalysisSummary.region_type == "state"))
        return list(result.scalars().all())

    @staticmethod
    async def get_lga_summaries(db: AsyncSession, state_id: int) -> List[GapAnalysisSummary]:
        """AC 193: LGA summaries for a state"""
        result = await db.execute(
            select(GapAnalysisSummary).filter(
                and_(
                    GapAnalysisSummary.region_type == "lga",
                    GapAnalysisSummary.state_id == state_id
                )
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_partner_contributions(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        """AC 195: Partner-specific contributions"""
        result = await db.execute(select(Ambulance).where(Ambulance.partner_id == user_id))
        ambulances = result.scalars().all()
        return [
            {
                "id": a.id,
                "plate_number": a.plate_number,
                "make_model": a.make_model,
                "status": a.status,
                "latitude": a.last_latitude,
                "longitude": a.last_longitude
            }
            for a in ambulances
        ]
