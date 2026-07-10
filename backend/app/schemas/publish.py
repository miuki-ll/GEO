"""发布任务 — 对齐 models/publish.py。"""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import Field, model_validator

from app.schemas.common import BaseSchema, IDModel, TimestampResponse, PaginationParams
from app.schemas._helpers import orm_to_metadata_dict


class PublishTaskBase(BaseSchema):
    content_asset_id: int = Field(..., alias="draft_id")
    channel: str = "hosted"
    mode: str = "auto"
    target_url: Optional[str] = None
    metadata_: Dict[str, Any] = Field(default_factory=dict, alias="metadata")

    @model_validator(mode="before")
    @classmethod
    def _fix_orm(cls, data):
        data = orm_to_metadata_dict(data)
        if isinstance(data, dict) and "content_asset_id" in data and "draft_id" not in data:
            data["draft_id"] = data["content_asset_id"]
        return data


class PublishTaskCreate(PublishTaskBase):
    pass


class PublishTaskUpdate(BaseSchema):
    published_url: Optional[str] = None
    published_id: Optional[str] = None
    status: Optional[str] = None
    retry_count: Optional[int] = None
    error_message: Optional[str] = None
    published_at: Optional[datetime] = None
    metadata_: Optional[Dict[str, Any]] = Field(default=None, alias="metadata")

    @model_validator(mode="before")
    @classmethod
    def _fix_orm(cls, data):
        return orm_to_metadata_dict(data)


class PublishTaskResponse(PublishTaskBase, IDModel, TimestampResponse):
    enterprise_id: int
    status: str = "pending"
    retry_count: int = 0
    fallback_semi: bool = False
    utm_content: Optional[str] = None
    error_message: Optional[str] = None
    published_url: Optional[str] = None
    published_id: Optional[str] = None
    published_at: Optional[datetime] = None


class PublishTaskListParams(PaginationParams):
    draft_id: Optional[int] = None
    channel: Optional[str] = None
    mode: Optional[str] = None
    status: Optional[str] = None
