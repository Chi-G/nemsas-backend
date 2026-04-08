from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models.incident import Incident, QAFinding
from src.schemas.incident import QAFindingCreate
from datetime import datetime, timezone
from typing import List, Optional, Any

class QAService:
    @staticmethod
    async def create_finding(
        db: AsyncSession, obj_in: QAFindingCreate, officer_id: int
    ) -> QAFinding:
        # Check if incident exists
        incident = await db.get(Incident, obj_in.incident_id)
        if not incident:
            raise Exception("Incident not found")
            
        # Enforce mandatory findings for Non-Compliant
        if obj_in.compliance_rating == "Non-Compliant" and not obj_in.findings_text:
            raise Exception("Findings text is mandatory for non-compliant rating")
            
        db_obj = QAFinding(
            incident_id=obj_in.incident_id,
            compliance_rating=obj_in.compliance_rating, 
            findings_text=obj_in.findings_text,
            qa_officer_id=officer_id,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def get_findings_by_incident(db: AsyncSession, incident_id: int) -> List[QAFinding]:
        result = await db.execute(select(QAFinding).where(QAFinding.incident_id == incident_id))
        return result.scalars().all()

qa_service = QAService()
