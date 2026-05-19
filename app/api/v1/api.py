from fastapi import APIRouter
from app.api.v1.endpoints import (
    users, states, lgas, wards, roles, auth,
    hospital_types, ambulance_types, hospitals, ambulances, organisations,
    incidents, claims, run_sheets, monitoring, incident_types, websockets,
    medical_interventions, fee_categories, services, devices, dashboard,
    patient_transfer_forms
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(organisations.router, prefix="/organisations", tags=["organisations"])
api_router.include_router(hospital_types.router, prefix="/hospital-types", tags=["hospital-types"])
api_router.include_router(ambulance_types.router, prefix="/ambulance-types", tags=["ambulance-types"])
api_router.include_router(hospitals.router, prefix="/hospitals", tags=["hospitals"])
api_router.include_router(ambulances.router, prefix="/ambulances", tags=["ambulances"])
api_router.include_router(states.router, prefix="/states", tags=["states"])
api_router.include_router(lgas.router, prefix="/lgas", tags=["lgas"])
api_router.include_router(wards.router, prefix="/wards", tags=["wards"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(fee_categories.router, prefix="/fee-categories", tags=["fee-categories"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(incident_types.router, prefix="/incident-types", tags=["incident-types"])
api_router.include_router(medical_interventions.router, prefix="/medical-interventions", tags=["medical-interventions"])

# Operations Resource Map
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(claims.router, prefix="/claims", tags=["claims"])
api_router.include_router(run_sheets.router, prefix="/run-sheets", tags=["runsheets"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(patient_transfer_forms.router, prefix="/TransferForms", tags=["TransferForms"])
api_router.include_router(websockets.router, prefix="/ws", tags=["websockets"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
