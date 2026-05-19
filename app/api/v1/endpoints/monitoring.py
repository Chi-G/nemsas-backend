import calendar
from typing import Any, List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.crud.monitoring import monitoring as crud_monitoring

from app.schemas.monitoring import MonthlyAggregateResponse

router = APIRouter()

@router.get("/", response_model=MonthlyAggregateResponse)
async def read_monitoring(
    db: AsyncSession = Depends(deps.get_db),
    year: Optional[int] = None
) -> Any:
    """
    Returns monthly analytics grids.
    """
    items = await crud_monitoring.get_monthly_aggregates(db, year=year)
    
    data = []
    for row in items:
        # Map integer month to full month name (e.g. 1 -> "January")
        month_name = calendar.month_name[row.month] if row.month and 1 <= row.month <= 12 else "Unknown"
        
        data.append({
            "month": month_name,
            "noOfTransport": int(row.noOfTransport or 0),
            "noOfMamiiLGAs": int(row.noOfMamiiLGAs or 0),
            "byTricycleAmbulance": int(row.byTricycleAmbulance or 0),
            "byNurtwDriver": int(row.byNurtwDriver or 0),
            "bls": int(row.bls or 0),
            "laborTransportation": int(row.laborTransportation or 0),
            "obstetricTransportation": int(row.obstetricTransportation or 0),
            "neonatalTransportation": int(row.neonatalTransportation or 0),
            "bemonc": int(row.bemonc or 0),
            "cemonc": int(row.cemonc or 0),
            "maternalMortalities": int(row.maternalMortalities or 0),
            "neonatalMortalities": int(row.neonatalMortalities or 0)
        })
        
    return {
        "message": "Monthly data fetched successfully",
        "data": data
    }
