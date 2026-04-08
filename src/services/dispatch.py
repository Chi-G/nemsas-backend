from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models.ambulance import Ambulance, Dispatch, AmbulanceStatus
from src.db.models.incident import Incident, IncidentStatus
from src.services.incident import incident_service
from src.services.ambulance import ambulance_service
from datetime import datetime, timezone
from typing import List, Optional, Any
import math

class DispatchService:
    @staticmethod
    async def get_nearest_ambulances(
        db: AsyncSession, latitude: float, longitude: float, limit: int = 5
    ) -> List[Ambulance]:
        # In a real implementation, this would use PostGIS or a Google Maps Distance Matrix API call.
        # For now, we perform a simple Euclidean distance approximation in the database query.
        # Since I'm using a simple relational DB, I'll fetch and sort in Python or use a basic SQL formula.
        
        result = await db.execute(
            select(Ambulance).where(Ambulance.status == AmbulanceStatus.ACTIVE)
        )
        ambulances = result.scalars().all()
        
        # Sort by simple distance
        # dist = sqrt((x2-x1)^2 + (y2-y1)^2)
        def calculate_dist(amb):
            if amb.last_latitude is None or amb.last_longitude is None:
                return float('inf')
            return math.sqrt((amb.last_latitude - latitude)**2 + (amb.last_longitude - longitude)**2)
            
        ambulances = sorted(ambulances, key=calculate_dist)
        return ambulances[:limit]

    @staticmethod
    async def assign_ambulances(
        db: AsyncSession, incident_id: int, ambulance_ids: List[int], current_user_id: int
    ) -> List[Dispatch]:
        incident = await db.get(Incident, incident_id)
        if not incident:
            raise Exception("Incident not found")
            
        dispatches = []
        for amb_id in ambulance_ids:
            ambulance = await ambulance_service.get_by_id(db, ambulance_id=amb_id)
            if not ambulance or ambulance.status != AmbulanceStatus.ACTIVE:
                continue
                
            dispatch = Dispatch(
                incident_id=incident_id,
                ambulance_id=amb_id,
                crew_id=current_user_id, # Simplified: in reality, crew might be separate from the actor
                dispatch_timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            db.add(dispatch)
            
            # Update ambulance status
            ambulance.status = AmbulanceStatus.ON_DUTY
            dispatches.append(dispatch)
            
        # Update incident status
        await incident_service.update_status(
            db, db_obj=incident, new_status=IncidentStatus.DISPATCHED, changer_id=current_user_id
        )
        
        await db.commit()
        return dispatches

dispatch_service = DispatchService()
