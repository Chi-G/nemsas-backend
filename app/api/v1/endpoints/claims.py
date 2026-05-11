from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.schemas.claim import ClaimPaginatedResponse, ClaimResponse
from app.crud.claim import claim as crud_claim
from app.crud.claim_setting import claim_setting as crud_setting
from app.schemas.claim_setting import ClaimSetting
from typing import List

router = APIRouter()

@router.get("/", response_model=ClaimPaginatedResponse)
async def read_claims(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    query: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None
) -> Any:
    """
    Get claims for ambulances or etc.
    Supports standard filtering parameters provided by the user workflow.
    """
    items, total = await crud_claim.get_multi_with_count(
        db,
        skip=skip,
        limit=limit,
        status=status,
        query_review=query,
        year=year,
        month=month
    )
    return {
        "success": True,
        "message": "Claim(s) successfully fetched",
        "data": {"items": items},
        "totalCount": total
    }

@router.get("/settings")
async def read_claim_settings(
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Global retrieval of expiration controls and thresholds.
    """
    configs = await crud_setting.get_all(db)
    # Reformat to plain dictionary or list as needed, maintaining client compatibility.
    return configs

@router.get("/{id}", response_model=ClaimResponse)
async def read_claim(
    id: int,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    item = await crud_claim.get(db, id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {
        "success": True,
        "message": "Claim successfully fetched",
        "data": item
    }
