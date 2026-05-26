import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.state import State
from app.models.monitoring import Monitoring

@pytest_asyncio.fixture
async def setup_monitoring_data(db: AsyncSession):
    # Clean up existing monitoring records
    await db.execute(delete(Monitoring))
    await db.commit()

    # Seed states if not exist
    state_37 = await db.get(State, 37)
    if not state_37:
        state_37 = State(id=37, name="Zamfara", code="")
        db.add(state_37)

    state_8 = await db.get(State, 8)
    if not state_8:
        state_8 = State(id=8, name="Borno", code="")
        db.add(state_8)

    await db.flush()

    # Seed monitoring records
    mon1 = Monitoring(
        year=2010,
        month=1,
        no_of_transport=12,
        no_of_mamii_lgas=34,
        by_tricycle_ambulance=2,
        by_nurtw_driver=23,
        bls=12,
        labor_transportation=34,
        obstetric_transportation=43,
        neonatal_transportation=12,
        bemonc=34,
        cemonc=2233,
        maternal_mortalities=12,
        neonatal_mortalities=34,
        remark="boom",
        state_id=37,
        added_by="AhmedNemsas NemsasAhmed NemsasAhmedUser",
        is_active=True
    )

    mon2 = Monitoring(
        year=2025,
        month=12,
        no_of_transport=535,
        no_of_mamii_lgas=5,
        by_tricycle_ambulance=2,
        by_nurtw_driver=224,
        bls=310,
        labor_transportation=527,
        obstetric_transportation=6,
        neonatal_transportation=2,
        bemonc=525,
        cemonc=9,
        maternal_mortalities=0,
        neonatal_mortalities=0,
        remark="Satisfactory",
        state_id=8,
        added_by="Kaka Mahdi Gazali",
        is_active=True
    )

    db.add_all([mon1, mon2])
    await db.commit()

@pytest.mark.asyncio
async def test_get_all_monitoring_records(client: AsyncClient, setup_monitoring_data):
    response = await client.get("/api/v1/monitoring/")
    assert response.status_code == 200
    
    payload = response.json()
    assert payload["success"] is True
    assert "data" in payload
    
    data = payload["data"]
    assert len(data) == 2

    # Verify keys matching monitoring.json format
    zamfara_rec = next(item for item in data if item["stateId"] == 37)
    assert zamfara_rec["year"] == 2010
    assert zamfara_rec["month"] == 1
    assert zamfara_rec["noOfTransport"] == 12
    assert zamfara_rec["noOfMamiiLGAs"] == 34
    assert zamfara_rec["byTricycleAmbulance"] == 2
    assert zamfara_rec["byNurtwDriver"] == 23
    assert zamfara_rec["bls"] == 12
    assert zamfara_rec["laborTransportation"] == 34
    assert zamfara_rec["obstetricTransportation"] == 43
    assert zamfara_rec["neonatalTransportation"] == 12
    assert zamfara_rec["bemonc"] == 34
    assert zamfara_rec["cemonc"] == 2233
    assert zamfara_rec["maternalMortalities"] == 12
    assert zamfara_rec["neonatalMortalities"] == 34
    assert zamfara_rec["remark"] == "boom"
    assert zamfara_rec["addedBy"] == "AhmedNemsas NemsasAhmed NemsasAhmedUser"
    assert zamfara_rec["isActive"] is True
    assert "updatedAt" in zamfara_rec
    assert "updatedBy" in zamfara_rec

    # Verify nested state object format
    state = zamfara_rec["state"]
    assert state is not None
    assert state["id"] == 37
    assert state["name"] == "Zamfara"
    assert state["code"] == ""
    assert state["lgas"] == []
    assert "dateAdded" in state
    assert "addedBy" in state
    assert "updatedAt" in state
    assert "updatedBy" in state
    assert "isActive" in state

@pytest.mark.asyncio
async def test_get_monitoring_records_filtering(client: AsyncClient, setup_monitoring_data):
    # Filter by Year
    resp_year = await client.get("/api/v1/monitoring/?year=2025")
    assert resp_year.status_code == 200
    data_year = resp_year.json()["data"]
    assert len(data_year) == 1
    assert data_year[0]["year"] == 2025

    # Filter by Month
    resp_month = await client.get("/api/v1/monitoring/?month=1")
    assert resp_month.status_code == 200
    data_month = resp_month.json()["data"]
    assert len(data_month) == 1
    assert data_month[0]["month"] == 1

    # Filter by State ID
    resp_state = await client.get("/api/v1/monitoring/?stateId=8")
    assert resp_state.status_code == 200
    data_state = resp_state.json()["data"]
    assert len(data_state) == 1
    assert data_state[0]["stateId"] == 8

    # Filter by All
    resp_all = await client.get("/api/v1/monitoring/?year=2025&month=12&stateId=8")
    assert resp_all.status_code == 200
    data_all = resp_all.json()["data"]
    assert len(data_all) == 1
    assert data_all[0]["stateId"] == 8
    assert data_all[0]["year"] == 2025
    assert data_all[0]["month"] == 12

    # Filter with no match
    resp_none = await client.get("/api/v1/monitoring/?year=2025&month=1")
    assert resp_none.status_code == 200
    data_none = resp_none.json()["data"]
    assert len(data_none) == 0
