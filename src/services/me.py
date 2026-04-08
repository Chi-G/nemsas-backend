from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.db.models.ambulance import Ambulance, AmbulanceStatus
from src.db.models.partner import Pledge, PledgeStatus
from typing import List, Optional, Any, Dict

class MEService:
    @staticmethod
    async def get_national_summary(db: AsyncSession) -> Dict[str, Any]:
        # Constants from requirements
        POPULATION_RATIO = 50000
        TOTAL_POPULATION = 200000000 # Placeholder for actual NPC data
        
        target = TOTAL_POPULATION // POPULATION_RATIO
        
        # Count active ambulances
        active_count = await db.scalar(
            select(func.count(Ambulance.id)).where(Ambulance.status == AmbulanceStatus.ACTIVE)
        )
        
        # Count pledged ambulances
        pledged_count = await db.scalar(
            select(func.sum(Pledge.ambulance_count)).where(Pledge.status != PledgeStatus.REJECTED)
        ) or 0
        
        return {
            "national_target": target,
            "total_active": active_count,
            "total_pledged": pledged_count,
            "gap": max(0, target - active_count),
            "coverage_percentage": (active_count / target * 100) if target > 0 else 0
        }

    @staticmethod
    async def get_state_summary(db: AsyncSession, state_id: int) -> Dict[str, Any]:
        # Simplified state-level data
        # In reality, would join with a 'states' table containing population
        STATE_POPULATION = 5000000 # Placeholder
        target = STATE_POPULATION // 50000
        
        active_count = await db.scalar(
            select(func.count(Ambulance.id)).where(
                Ambulance.state_id == state_id, 
                Ambulance.status == AmbulanceStatus.ACTIVE
            )
        )
        
        return {
            "state_id": state_id,
            "population": STATE_POPULATION,
            "target": target,
            "active_ambulances": active_count,
            "gap": max(0, target - active_count),
            "coverage_percentage": (active_count / target * 100) if target > 0 else 0
        }

me_service = MEService()
