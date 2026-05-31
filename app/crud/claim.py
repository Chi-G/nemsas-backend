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
            selectinload(Claim.patient).selectinload(PatientModel.etc_interventions),
            selectinload(Claim.images),
            selectinload(Claim.incident).selectinload(Incident.patients).selectinload(PatientModel.interventions),
            selectinload(Claim.incident).selectinload(Incident.patients).selectinload(PatientModel.etc_interventions),
            selectinload(Claim.incident).selectinload(Incident.hospital).selectinload(HospitalModel.hospital_type),
            selectinload(Claim.incident).selectinload(Incident.hospital).selectinload(HospitalModel.state),
            selectinload(Claim.incident).selectinload(Incident.hospital).selectinload(HospitalModel.lga),
            selectinload(Claim.incident).selectinload(Incident.incident_type),
            selectinload(Claim.incident).selectinload(Incident.state),
            selectinload(Claim.incident).selectinload(Incident.claims).selectinload(ClaimModel.images),
            # Required: Incident schema model_validator reads etc_interventions to split into drugs/procedures per patient
            selectinload(Claim.incident).selectinload(Incident.etc_interventions),
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
        db.expunge(db_obj)
        stmt = select(Claim).options(*self._get_claim_options()).where(Claim.id == db_obj.id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get(self, db: AsyncSession, id: int) -> Optional[Claim]:
        stmt = select(Claim).options(*self._get_claim_options()).where(Claim.id == id).execution_options(populate_existing=True)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_multi_with_count(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None,
        query_review: Optional[str] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        is_etc: Optional[bool] = None,
        ambulance_id: Optional[int] = None,
        state_id: Optional[int] = None,
        etc_id: Optional[int] = None,
        incident_category_id: Optional[int] = None
    ) -> Tuple[List[Claim], int]:
        base_filters = []
        
        if status:
            if is_etc is True:
                base_filters.append(Claim.etc_claim_status.ilike(status))
            elif is_etc is False:
                base_filters.append(Claim.ambulance_claim_status.ilike(status))
            else:
                base_filters.append((Claim.ambulance_claim_status.ilike(status)) | (Claim.etc_claim_status.ilike(status)))
            
        if query_review:
            if is_etc is True:
                base_filters.append(Claim.etc_review.ilike(f"%{query_review}%"))
            elif is_etc is False:
                base_filters.append(Claim.review.ilike(f"%{query_review}%"))
            else:
                base_filters.append((Claim.review.ilike(f"%{query_review}%")) | (Claim.etc_review.ilike(f"%{query_review}%")))

        if year is not None:
            base_filters.append(extract('year', Incident.date_added) == year)
            
        if month is not None:
            base_filters.append(extract('month', Incident.date_added) == month)

        # Note: We do not filter by claim_type because the same claim record is used for both ETC and Ambulance.

        stmt = select(Claim).options(*self._get_claim_options()).order_by(desc(Claim.id))
        count_stmt = select(func.count()).select_from(Claim)
        
        need_incident_join = (ambulance_id is not None) or (state_id is not None) or (etc_id is not None) or (incident_category_id is not None) or (year is not None) or (month is not None) or (search is not None)
        if need_incident_join:
            stmt = stmt.join(Claim.incident)
            count_stmt = count_stmt.join(Claim.incident)
            
            if search is not None:
                from app.models.hospital import Hospital
                from app.models.ambulance import Ambulance
                from sqlalchemy import or_
                
                stmt = stmt.outerjoin(Hospital, Incident.etc_id == Hospital.id)
                stmt = stmt.outerjoin(Ambulance, Incident.ambulance_id == Ambulance.id)
                
                count_stmt = count_stmt.outerjoin(Hospital, Incident.etc_id == Hospital.id)
                count_stmt = count_stmt.outerjoin(Ambulance, Incident.ambulance_id == Ambulance.id)
                
                base_filters.append(
                    or_(
                        Claim.patient_name.ilike(f"%{search}%"),
                        Hospital.name.ilike(f"%{search}%"),
                        Ambulance.name.ilike(f"%{search}%")
                    )
                )
            
        if ambulance_id is not None:
            base_filters.append(Incident.ambulance_id == ambulance_id)
            
        if state_id is not None:
            base_filters.append(Incident.state_id == state_id)
            
        if etc_id is not None:
            base_filters.append(Incident.etc_id == etc_id)

        if incident_category_id is not None:
            base_filters.append(Incident.incident_category_id == incident_category_id)
        
        if base_filters:
            stmt = stmt.where(and_(*base_filters))
            count_stmt = count_stmt.where(and_(*base_filters))
            
        total_count = await db.scalar(count_stmt)
        result = await db.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all()), total_count or 0

    async def get_summary(self, db: AsyncSession, state_id: Optional[int] = None, ambulance_id: Optional[int] = None, etc_id: Optional[int] = None, user_type: Optional[str] = None) -> dict:
        need_incident_join = (state_id is not None) or (ambulance_id is not None) or (etc_id is not None)
        
        def calculate_counts(rows):
            counts = {row[0]: row[1] for row in rows}
            approved = counts.get("Approved", 0) + counts.get("approved", 0) + counts.get("Endorsed", 0) + counts.get("endorsed", 0)
            rejected = counts.get("Rejected", 0) + counts.get("rejected", 0)
            pending = counts.get("Pending", 0) + counts.get("pending", 0) + counts.get("New", 0) + counts.get("new", 0)
            total = sum(counts.values())
            return {
                "total": total,
                "approved": approved,
                "rejected": rejected,
                "pending": pending
            }

        zero_stats = {
            "total": 0,
            "approved": 0,
            "rejected": 0,
            "pending": 0
        }

        if user_type == "AMBULANCEUSER":
            stmt = select(Claim.ambulance_claim_status, func.count(Claim.id)).where((Claim.claim_type != "ETC") | (Claim.claim_type == None))
            if need_incident_join:
                stmt = stmt.join(Claim.incident)
                if ambulance_id is not None:
                    stmt = stmt.where(Incident.ambulance_id == ambulance_id)
            stmt = stmt.group_by(Claim.ambulance_claim_status)
            result = await db.execute(stmt)
            return {
                "ambulanceStatus": calculate_counts(result.all()),
                "etcStatus": zero_stats
            }
            
        elif user_type == "EMERGENCYTREATMENTUSER":
            stmt = select(Claim.etc_claim_status, func.count(Claim.id))
            if need_incident_join:
                stmt = stmt.join(Claim.incident)
                if etc_id is not None:
                    stmt = stmt.where(Incident.etc_id == etc_id)
            stmt = stmt.group_by(Claim.etc_claim_status)
            result = await db.execute(stmt)
            return {
                "ambulanceStatus": zero_stats,
                "etcStatus": calculate_counts(result.all())
            }
            
        else:
            # Admin: return both
            stmt_amb = select(Claim.ambulance_claim_status, func.count(Claim.id)).where((Claim.claim_type != "ETC") | (Claim.claim_type == None))
            if need_incident_join:
                stmt_amb = stmt_amb.join(Claim.incident)
                if state_id is not None:
                    stmt_amb = stmt_amb.where(Incident.state_id == state_id)
            stmt_amb = stmt_amb.group_by(Claim.ambulance_claim_status)
            res_amb = await db.execute(stmt_amb)
            amb_stats = calculate_counts(res_amb.all())
            
            stmt_etc = select(Claim.etc_claim_status, func.count(Claim.id)).where(Claim.claim_type == "ETC")
            if need_incident_join:
                stmt_etc = stmt_etc.join(Claim.incident)
                if state_id is not None:
                    stmt_etc = stmt_etc.where(Incident.state_id == state_id)
            stmt_etc = stmt_etc.group_by(Claim.etc_claim_status)
            res_etc = await db.execute(stmt_etc)
            etc_stats = calculate_counts(res_etc.all())
            
            return {
                "ambulanceStatus": amb_stats,
                "etcStatus": etc_stats
            }

    async def remove(self, db: AsyncSession, *, id: int) -> Optional[Claim]:
        stmt = select(Claim).where(Claim.id == id)
        result = await db.execute(stmt)
        db_obj = result.scalars().first()
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj

claim = CRUDClaim()
