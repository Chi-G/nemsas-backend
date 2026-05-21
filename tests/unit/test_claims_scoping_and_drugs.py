import pytest
from app.schemas.claim import Claim

def test_claim_pydantic_mapping_etc():
    # Test ETC claim type maps interventions to details & medical_interventions, and drugs to drugs_list
    data = {
        "id": 1,
        "title": "ETC Claim Test",
        "claim_type": "ETC",
        "patient": {
            "id": 100,
            "interventions": [
                {
                    "id": 10,
                    "patient_id": 100,
                    "mediicalIntervention": "Intervention A",
                    "is_alert": False,
                    "can_speak": False,
                    "is_in_pain": False,
                    "un_responsive": False
                }
            ],
            "drugs": '[{"id": 100, "name": "Drug A"}]'
        }
    }
    
    claim = Claim.model_validate(data)
    assert claim.claim_type == "ETC"
    assert len(claim.details) == 1
    assert claim.details[0]["mediicalIntervention"] == "Intervention A"
    assert len(claim.medical_interventions) == 1
    assert claim.medical_interventions[0]["mediicalIntervention"] == "Intervention A"
    assert len(claim.drugs_list) == 1
    assert claim.drugs_list[0]["name"] == "Drug A"

def test_claim_pydantic_mapping_ambulance():
    # Test Ambulance claim type maps drugs to details & drugs_list, and interventions to medical_interventions (which should be empty)
    data = {
        "id": 2,
        "title": "Ambulance Claim Test",
        "claim_type": "Ambulance",
        "patient": {
            "id": 200,
            "interventions": [
                {
                    "id": 10,
                    "patient_id": 200,
                    "mediicalIntervention": "Intervention A",
                    "is_alert": False,
                    "can_speak": False,
                    "is_in_pain": False,
                    "un_responsive": False
                }
            ],
            "drugs": '[{"id": 200, "name": "Drug B"}]'
        }
    }
    
    claim = Claim.model_validate(data)
    assert claim.claim_type == "Ambulance"
    assert len(claim.details) == 1
    assert claim.details[0]["name"] == "Drug B"
    assert len(claim.medical_interventions) == 0
    assert len(claim.drugs_list) == 1
    assert claim.drugs_list[0]["name"] == "Drug B"
