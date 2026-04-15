import pytest
from src.services.reference import reference_service
from src.db.models.reference import Drug, State, LGA, SystemAuditLog
from src.schemas.reference import DrugCreate, DrugUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

@pytest.mark.asyncio
async def test_drug_deactivation_logic(db: AsyncSession):
    # Setup
    drug = Drug(name="Test Aspirin", dosage_form="Tablet")
    db.add(drug)
    await db.commit()
    await db.refresh(drug)
    
    # Deactivate
    update_in = DrugUpdate(is_active=False)
    updated = await reference_service.update_drug(db, drug_id=drug.id, obj_in=update_in, user_id=1)
    
    assert updated.is_active is False
    
    # Check Audit Log
    stmt = select(SystemAuditLog).where(SystemAuditLog.record_id == drug.id, SystemAuditLog.table_name == "drugs")
    res = await db.execute(stmt)
    audit = res.scalars().first()
    assert audit is not None
    assert audit.action == "DEACTIVATE"
    assert audit.changes["is_active"]["new"] is False

@pytest.mark.asyncio
async def test_geography_hierarchy_logic(db: AsyncSession):
    # Setup
    state = State(name="Reference State")
    db.add(state)
    await db.flush()
    lga = LGA(name="Reference LGA", state_id=state.id)
    db.add(lga)
    await db.commit()
    
    hierarchy = await reference_service.get_state_lga_hierarchy(db)
    target = next((s for s in hierarchy if s.name == "Reference State"), None)
    assert target is not None
    assert len(target.lgas) >= 1
    assert target.lgas[0].name == "Reference LGA"
