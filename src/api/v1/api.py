from fastapi import APIRouter
from src.api.v1 import (
    auth, users, incidents, ambulances, dispatch, run_sheets, 
    etc, claims, qa, reference, partners, me, ussd_sms
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(ambulances.router, prefix="/ambulances", tags=["ambulances"])
api_router.include_router(dispatch.router, prefix="/dispatch", tags=["dispatch"])
api_router.include_router(run_sheets.router, prefix="/run-sheets", tags=["run-sheets"])
api_router.include_router(etc.router, prefix="/etc", tags=["etc"])
api_router.include_router(claims.router, prefix="/claims", tags=["claims"])
api_router.include_router(qa.router, prefix="/qa", tags=["qa"])
api_router.include_router(reference.router, prefix="/reference", tags=["reference"])
api_router.include_router(partners.router, prefix="/partners", tags=["partners"])
api_router.include_router(me.router, prefix="/m-e", tags=["m-e"])
api_router.include_router(ussd_sms.router, prefix="/ussd-sms", tags=["ussd-sms"])
