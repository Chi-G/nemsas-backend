from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from src.db.models.incident import Incident, IncidentStatus, IncidentStatusHistory, QAFinding, ComplianceRating
from src.db.models.ambulance import Dispatch, Ambulance
from src.schemas.qa import QAFilter, QAIncidentSummary, QAFindingCreate
from datetime import datetime, timezone
from typing import List, Optional, Any

class QAService:
    @staticmethod
    async def get_qa_incidents_paginated(
        db: AsyncSession,
        filters: QAFilter,
        skip: int = 0,
        limit: int = 100,
        state_id: Optional[int] = None
    ) -> List[QAIncidentSummary]:
        # Filter for only Completed or Closed incidents
        stmt = select(Incident).where(Incident.status.in_([IncidentStatus.COMPLETED, IncidentStatus.CLOSED]))
        
        # Scoping
        if state_id:
            stmt = stmt.where(Incident.state_id == state_id)
        elif filters.state_id:
            stmt = stmt.where(Incident.state_id == filters.state_id)
            
        if filters.lga_id:
            stmt = stmt.where(Incident.lga_id == filters.lga_id)
            
        if filters.date_from:
            stmt = stmt.where(Incident.created_at >= filters.date_from)
        if filters.date_to:
            stmt = stmt.where(Incident.created_at <= filters.date_to)
            
        if filters.ambulance_id:
            stmt = stmt.join(Dispatch).where(Dispatch.ambulance_id == filters.ambulance_id)

        stmt = stmt.order_by(desc(Incident.created_at)).offset(skip).limit(limit)
        
        # Eager load relationships for response time and findings
        stmt = stmt.options(
            selectinload(Incident.status_history),
            selectinload(Incident.dispatches)
        )
        
        result = await db.execute(stmt)
        incidents = result.scalars().all()
        
        summaries = []
        for inc in incidents:
            # 1. Calculate Response Time
            # Dispatch time from Dispatch model
            dispatch_time = None
            if inc.dispatches:
                dispatch_time = inc.dispatches[0].dispatch_timestamp
                
            # Arrival time from Status History
            arrival_time = None
            at_scene_entry = next((h for h in inc.status_history if h.status == IncidentStatus.AT_SCENE), None)
            if at_scene_entry:
                arrival_time = at_scene_entry.changed_at
                
            response_time_min = None
            if dispatch_time and arrival_time:
                delta = arrival_time - dispatch_time
                response_time_min = delta.total_seconds() / 60.0
                
            # 2. Get Ambulance Info
            ambulance_plate = None
            if inc.dispatches:
                # Need to fetch ambulance plate if not loaded.
                amb_res = await db.execute(select(Ambulance).where(Ambulance.id == inc.dispatches[0].ambulance_id))
                amb = amb_res.scalars().first()
                if amb:
                    ambulance_plate = amb.plate_number
            
            # 3. Get latest Compliance status
            finding_stmt = select(QAFinding).where(QAFinding.incident_id == inc.id).order_by(desc(QAFinding.created_at)).limit(1)
            f_res = await db.execute(finding_stmt)
            latest_finding = f_res.scalars().first()
            
            # Filter by compliance status if requested
            if filters.compliance_rating and (not latest_finding or latest_finding.compliance_rating != filters.compliance_rating):
                continue

            summaries.append(QAIncidentSummary(
                id=inc.id,
                uuid=inc.uuid,
                location_label=inc.location_label,
                emergency_type=inc.emergency_type,
                status=inc.status,
                created_at=inc.created_at,
                response_time_minutes=response_time_min,
                ambulance_plate=ambulance_plate,
                latest_compliance_status=latest_finding.compliance_rating if latest_finding else None,
                has_findings=latest_finding is not None
            ))
            
        return summaries

    @staticmethod
    async def create_finding(
        db: AsyncSession, obj_in: QAFindingCreate, officer_id: int, state_id: Optional[int] = None
    ) -> QAFinding:
        # Check if incident exists
        incident = await db.get(Incident, obj_in.incident_id)
        if not incident:
            raise Exception("Incident not found")
        
        if state_id and incident.state_id != state_id:
            raise Exception("Access denied: Incident belongs to another state")
            
        # Requirement Check: Non-Compliant rating requires non-empty findings text
        if obj_in.compliance_rating == ComplianceRating.NON_COMPLIANT and not obj_in.findings_text.strip():
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
    async def get_findings_by_incident(db: AsyncSession, incident_id: int, state_id: Optional[int] = None) -> List[QAFinding]:
        stmt = select(QAFinding).where(QAFinding.incident_id == incident_id)
        if state_id:
            stmt = stmt.join(Incident).where(Incident.state_id == state_id)
        
        stmt = stmt.order_by(desc(QAFinding.created_at))
        result = await db.execute(stmt)
        return result.scalars().all()

qa_service = QAService()
