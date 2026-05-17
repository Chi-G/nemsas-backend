from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, and_, extract
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple, Any
from app.models.claim import Claim
from app.models.incident import Incident
from app.schemas.claim import ClaimCreate

class CRUDClaim:
    def _get_claim_options(self) -> List[Any]:
        from app.models.patient import Patient as PatientModel
        from app.models.hospital import Hospital as HospitalModel
        from app.models.claim import Claim as ClaimModel
        
        return [
            selectinload(Claim.patient).selectinload(PatientModel.interventions),
            selectinload(Claim.images),
            selectinload(Claim.incident).selectinload(Incident.patients).selectinload(PatientModel.interventions),
            selectinload(Claim.incident).selectinload(Incident.hospital).selectinload(HospitalModel.hospital_type),
            selectinload(Claim.incident).selectinload(Incident.hospital).selectinload(HospitalModel.state),
            selectinload(Claim.incident).selectinload(Incident.hospital).selectinload(HospitalModel.lga),
            selectinload(Claim.incident).selectinload(Incident.incident_type),
            selectinload(Claim.incident).selectinload(Incident.state),
            selectinload(Claim.incident).selectinload(Incident.claims).selectinload(ClaimModel.images)
        ]

    async def create(self, db: AsyncSession, *, obj_in: ClaimCreate, current_user: Optional[Any] = None) -> Claim:
        obj_in_data = obj_in.model_dump()
        image_url = obj_in_data.pop("image_url", None)
        
        db_obj = Claim(**obj_in_data)
        
        is_etc = False
        if current_user:
            db_obj.user_id = current_user.id
            user_type = getattr(current_user, "user_type", None)
            if user_type in ["SEMSASDISPATCH", "NEMSASUSER", "EMERGENCYTREATMENTUSER"]:
                is_etc = True
                db_obj.claim_type = "ETC"
            else:
                is_etc = False
                db_obj.claim_type = "Ambulance"
        else:
            db_obj.claim_type = "Ambulance"
            
        db.add(db_obj)
        await db.commit()
        
        # Check if a valid image URL was actually supplied
        if image_url and str(image_url).strip() and str(image_url).lower() != "null":
            from app.models.claim import ClaimImage
            
            # Find next image ID
            max_id_stmt = select(func.max(ClaimImage.id))
            max_id = await db.scalar(max_id_stmt) or 0
            new_image_id = max_id + 1
            
            db_image = ClaimImage(
                id=new_image_id,
                claim_id=db_obj.id,
                claim_title=db_obj.title,
                incident_id=db_obj.incident_id,
                image_url=image_url,
                is_etc=is_etc
            )
            db.add(db_image)
            await db.commit()
            
        # Eagerly load the claim with all relations to prevent any downstream lazy-loading / greenlet errors
        stmt = select(Claim).options(*self._get_claim_options()).where(Claim.id == db_obj.id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get(self, db: AsyncSession, id: int) -> Optional[Claim]:
        stmt = select(Claim).options(*self._get_claim_options()).where(Claim.id == id)
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
            base_filters.append(Claim.review.ilike(f"%{query_review}%"))

        if year and month:
            pass

        if is_etc is True:
            pass

        stmt = select(Claim).options(*self._get_claim_options()).order_by(desc(Claim.id))
        
        count_stmt = select(func.count()).select_from(Claim)
        
        if base_filters:
            stmt = stmt.where(and_(*base_filters))
            count_stmt = count_stmt.where(and_(*base_filters))
            
        total_count = await db.scalar(count_stmt)
        result = await db.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all()), total_count or 0

claim = CRUDClaim()
