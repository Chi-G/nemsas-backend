from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.api import deps
from app.schemas.fee_category import FeeCategory, FeeCategoryCreate, FeeCategoryUpdate
from app.schemas.common import ResponseBase
from app.models.fee_category import FeeCategory as FeeCategoryModel
from sqlalchemy.future import select

router = APIRouter()

@router.get("/", response_model=ResponseBase[List[FeeCategory]])
async def read_fee_categories(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=1000)
):
    result = await db.execute(
        select(FeeCategoryModel)
        .order_by(FeeCategoryModel.id)
        .offset(skip)
        .limit(limit)
    )
    categories = result.scalars().all()
    return {
        "success": True,
        "message": "Fee categories successfully fetched",
        "data": categories
    }
