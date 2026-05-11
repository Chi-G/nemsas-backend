import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from src.services.incident import incident_service
from src.db.models.incident import Incident, IncidentStatus
from src.core.constants import INCIDENT_TRANSITION_MAP

@pytest.mark.asyncio
async def test_incident_status_transition_valid():
    """Verify a valid transition (Created -> Dispatched)"""
    db = AsyncMock()
    incident = Incident(id=1, status=IncidentStatus.CREATED)
    
    # Mocking commit and refresh
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    
    updated = await incident_service.update_status(
        db, incident, IncidentStatus.DISPATCHED, changer_id=1
    )
    
    assert updated.status == IncidentStatus.DISPATCHED
    assert db.add.called  # IncidentStatusHistory added

@pytest.mark.asyncio
async def test_incident_status_transition_invalid():
    """Verify an invalid transition (Created -> Accepted) fails"""
    db = AsyncMock()
    incident = Incident(id=1, status=IncidentStatus.CREATED)
    
    with pytest.raises(HTTPException) as excinfo:
        await incident_service.update_status(
            db, incident, IncidentStatus.ACCEPTED, changer_id=1
        )
    
    assert excinfo.value.status_code == 422
    assert "Invalid status transition" in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_incident_closure_from_completed():
    """Verify closing from Completed is allowed."""
    db = AsyncMock()
    incident = Incident(id=1, status=IncidentStatus.COMPLETED)
    
    updated = await incident_service.update_status(
        db, incident, IncidentStatus.CLOSED, changer_id=1
    )
    assert updated.status == IncidentStatus.CLOSED

@pytest.mark.asyncio
async def test_location_search_mock():
    """Verify location search logic queries both Facilities and LGAs."""
    db = AsyncMock()
    
    # Mocking multiple results for Facilities and LGAs
    mock_facility = MagicMock(name="Facility")
    mock_facility.name = "Test Hospital"
    mock_facility.latitude = 1.0
    mock_facility.longitude = 2.0
    mock_facility.state_id = 1
    mock_facility.lga_id = 1
    
    mock_lga = MagicMock(name="LGA")
    mock_lga.name = "Test LGA"
    mock_lga.state_id = 1
    mock_lga.id = 1
    
    # Mock db.execute to return different results for different calls
    # 1. Facility search
    # 2. LGA search
    mock_res_fac = MagicMock()
    mock_res_fac.scalars.return_value.all.return_value = [mock_facility]
    
    mock_res_lga = MagicMock()
    mock_res_lga.scalars.return_value.all.return_value = [mock_lga]
    
    db.execute.side_effect = [mock_res_fac, mock_res_lga]
    
    results = await incident_service.search_locations(db, "Test")
    
    assert len(results) == 2
    assert results[0]["label"] == "Test Hospital"
    assert results[1]["label"] == "LGA: Test LGA"
