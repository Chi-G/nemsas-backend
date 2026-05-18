from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.api import deps
from app.schemas.service import Service, ServiceCreate, ServiceUpdate
from app.schemas.common import ResponseBase
from app.crud.service import service_crud

router = APIRouter()

@router.get("/", response_model=ResponseBase[List[Service]])
async def read_services(
    db: AsyncSession = Depends(deps.get_db),
    fee_category_id: int = Query(None, alias="feeCategoryId"),
    is_medicine: bool = Query(None, alias="isMedicine")
):
    services = await service_crud.get_all_services(
        db,
        fee_category_id=fee_category_id,
        is_medicine=is_medicine
    )
        
    return {
        "success": True,
        "message": "Service(s) successfully fetched",
        "data": services
    }


@router.get("/{id}", response_model=ResponseBase[Service])
async def read_service(
    id: int,
    db: AsyncSession = Depends(deps.get_db)
):
    service = await service_crud.get(db, id=id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    return {
        "success": True,
        "message": "Service successfully fetched",
        "data": service
    }

@router.post("/", response_model=ResponseBase[Service])
async def create_service(
    *,
    db: AsyncSession = Depends(deps.get_db),
    service_in: ServiceCreate,
):
    service = await service_crud.create(db, obj_in=service_in)
    return {
        "success": True,
        "message": "Service successfully created",
        "data": service
    }

@router.put("/{id}", response_model=ResponseBase[Service])
async def update_service(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
    service_in: ServiceUpdate
):
    service = await service_crud.get(db, id=id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    updated_service = await service_crud.update(db, db_obj=service, obj_in=service_in)
    return {
        "success": True,
        "message": "Service successfully updated",
        "data": updated_service
    }

@router.delete("/{id}", response_model=ResponseBase[Service])
async def delete_service(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int
):
    service = await service_crud.remove(db, id=id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    return {
        "success": True,
        "message": "Service successfully deleted",
        "data": service
    }
