from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, literal_column, union_all
from app.api import deps
from app.models.ambulance import Ambulance
from app.models.hospital import Hospital
from app.schemas.organisation import OrganisationResponse

router = APIRouter()

@router.get("/", response_model=OrganisationResponse)
async def read_organisations(
    db: AsyncSession = Depends(deps.get_db)
):
    # Create subqueries for both tables with a literal for organisationType
    amb_query = select(
        Ambulance.name,
        Ambulance.location,
        literal_column("'ASP'").label("organisationType")
    )
    
    hosp_query = select(
        Hospital.name,
        Hospital.location,
        literal_column("'ETC'").label("organisationType")
    )
    
    # Union them
    combined_query = union_all(amb_query, hosp_query).alias("organisations")
    
    # Final select with ordering (ASP first)
    final_query = select(
        combined_query.c.name,
        combined_query.c.location,
        combined_query.c.organisationType
    ).order_by(combined_query.c.organisationType.asc(), combined_query.c.name.asc())
    
    result = await db.execute(final_query)
    organisations = [
        {
            "name": row.name,
            "location": row.location,
            "organisationType": row.organisationType
        }
        for row in result.all()
    ]
    
    return {
        "success": True,
        "message": "Organisation(s) fetched",
        "data": organisations,
        "totalCount": len(organisations),
        "refreshToken": None
    }
