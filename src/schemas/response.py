from typing import TypeVar, Generic, Optional, Any, List
from pydantic import BaseModel

T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation successful"
    data: Optional[T] = None
    totalCount: int = 1
    refreshToken: Optional[str] = None
    refreshTokenExpiryTime: str = "0001-01-01T00:00:00"

class PaginatedData(BaseModel, Generic[T]):
    items: List[T]
    totalCount: int
    page: int
    pageSize: int
    totalPages: int
