from typing import Any, Generic, List, Optional, TypeVar, Dict
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

T = TypeVar("T")


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class IDModel(BaseSchema):
    id: int


class TimestampResponse(BaseSchema):
    created_at: datetime
    updated_at: datetime


class ResponseModel(BaseSchema, Generic[T]):
    code: int = 0
    message: str = "success"
    data: Optional[T] = None
    request_id: Optional[str] = None


class ListResponse(BaseSchema, Generic[T]):
    code: int = 0
    message: str = "success"
    total: int = 0
    page: int = 1
    page_size: int = 20
    items: List[T] = Field(default_factory=list)


class PaginationParams(BaseSchema):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=200)
    keyword: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "desc"


class MessageResponse(BaseSchema):
    message: str


class BulkIds(BaseSchema):
    ids: List[int]


ApiResponse = ResponseModel[Any]


class _PaginatedInner(BaseSchema):
    items: List[Any] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


PaginatedResponse = ResponseModel[_PaginatedInner]
