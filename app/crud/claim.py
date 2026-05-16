from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, and_, extract
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
from app.models.claim import Claim
from app.models.incident import Incident
from app.schemas.claim import ClaimCreate

class CRUDClaim:
    async def get(self, db: AsyncSession, id: int) -> Optional[Claim]:
        stmt = select(Claim).options(
            selectinload(Claim.patient),
            selectinload(Claim.incident).options(
                selectinload(Incident.patients),
                selectinload(Incident.incident_type),
                selectinload(Incident.state)
            )
        ).where(Claim.id == id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_multi_with_count(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        query_review: Optional[str] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        is_etc: Optional[bool] = None
    ) -> Tuple[List[Claim], int]:
        base_filters = []
        
        if status:
            base_filters.append(Claim.status.ilike(status))
            
        if query_review:
            # Supports multi-field textual search on review notes or explicit enum mapping if we set up that column.
            # User provided "filter by query" as a text search field. 
            base_filters.append(Claim.review.ilike(f"%{query_review}%"))

        if year and month:
            # Attempt extract from incident_date string or created_at. Let's fallback to created_at comparison
            # for precise filtering if incident_date contains inconsistent strings.
            pass

        if is_etc is True:
            # Check if etc_review is set or price is diff? Or just base it on AmbulanceType not being there.
            pass

        stmt = select(Claim).options(
            selectinload(Claim.patient),
            selectinload(Claim.incident).options(
                selectinload(Incident.patients),
                selectinload(Incident.incident_type),
                selectinload(Incident.state)
            )
        ).order_by(desc(Claim.id))
        
        count_stmt = select(func.count()).select_from(Claim)
        
        if base_filters:
            stmt = stmt.where(and_(*base_filters))
            count_stmt = count_stmt.where(and_(*base_filters))
            
        total_count = await db.scalar(count_stmt)
        result = await db.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all()), total_count or 0

claim = CRUDClaim()
