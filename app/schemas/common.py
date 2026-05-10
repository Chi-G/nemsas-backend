from pydantic import BaseModel
from typing import Generic, TypeVar, List, Optional, Any

T = TypeVar("T")

class ResponseBase(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: T

class PaginationMeta(BaseModel):
    total: int
    skip: int
    limit: int

class PaginatedResponse(ResponseBase[List[T]], Generic[T]):
    meta: Optional[PaginationMeta] = None
