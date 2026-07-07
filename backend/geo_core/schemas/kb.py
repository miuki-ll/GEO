from typing import Optional, List, Any
from pydantic import Field, model_validator
from datetime import datetime

from geo_core.schemas import BaseSchema, IDModel, TimestampResponse, PaginationParams


def _orm_to_metadata_dict(data: Any) -> Any:
    if isinstance(data, dict):
        return data
    d = {}
    if hasattr(data, "__dict__"):
        d = dict(data.__dict__)
        d.pop("_sa_instance_state", None)
    if hasattr(data, "metadata_"):
        d["metadata"] = data.metadata_ or {}
    return d


class KBFactBase(BaseSchema):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    source_type: str = "manual"
    source_ref: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata_: dict = Field(default_factory=dict, alias="metadata")

    @model_validator(mode="before")
    @classmethod
    def _fix_orm(cls, data):
        return _orm_to_metadata_dict(data)


class KBFactCreate(KBFactBase):
    verified: bool = False


class KBFactUpdate(BaseSchema):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = None
    source_type: Optional[str] = None
    source_ref: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    verified: Optional[bool] = None
    metadata_: Optional[dict] = Field(default=None, alias="metadata")

    @model_validator(mode="before")
    @classmethod
    def _fix_orm(cls, data):
        return _orm_to_metadata_dict(data)


class KBFactResponse(KBFactBase, IDModel, TimestampResponse):
    enterprise_id: int
    verified: bool
    embedding_id: Optional[str] = None


class KBFactListParams(PaginationParams):
    category: Optional[str] = None
    verified: Optional[bool] = None
    source_type: Optional[str] = None


class KBFaqBase(BaseSchema):
    question: str = Field(..., min_length=1, max_length=500)
    answer: str = Field(..., min_length=1)
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    fact_refs: List[int] = Field(default_factory=list)
    metadata_: dict = Field(default_factory=dict, alias="metadata")

    @model_validator(mode="before")
    @classmethod
    def _fix_orm(cls, data):
        return _orm_to_metadata_dict(data)


class KBFaqCreate(KBFaqBase):
    verified: bool = False


class KBFaqUpdate(BaseSchema):
    question: Optional[str] = Field(None, min_length=1, max_length=500)
    answer: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    fact_refs: Optional[List[int]] = None
    verified: Optional[bool] = None
    metadata_: Optional[dict] = Field(default=None, alias="metadata")

    @model_validator(mode="before")
    @classmethod
    def _fix_orm(cls, data):
        return _orm_to_metadata_dict(data)


class KBFaqResponse(KBFaqBase, IDModel, TimestampResponse):
    enterprise_id: int
    verified: bool
    embedding_id: Optional[str] = None


class KBFaqListParams(PaginationParams):
    category: Optional[str] = None
    verified: Optional[bool] = None


class KBSignalBase(BaseSchema):
    signal_type: str
    content: str = Field(..., min_length=1)
    source: Optional[str] = None
    confidence: int = Field(0, ge=0, le=100)
    fact_refs: List[int] = Field(default_factory=list)
    status: str = "pending"
    metadata_: dict = Field(default_factory=dict, alias="metadata")

    @model_validator(mode="before")
    @classmethod
    def _fix_orm(cls, data):
        return _orm_to_metadata_dict(data)


class KBSignalCreate(KBSignalBase):
    pass


class KBSignalUpdate(BaseSchema):
    signal_type: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = None
    confidence: Optional[int] = Field(None, ge=0, le=100)
    fact_refs: Optional[List[int]] = None
    status: Optional[str] = None
    metadata_: Optional[dict] = Field(default=None, alias="metadata")

    @model_validator(mode="before")
    @classmethod
    def _fix_orm(cls, data):
        return _orm_to_metadata_dict(data)


class KBSignalResponse(KBSignalBase, IDModel, TimestampResponse):
    enterprise_id: int


class KBSignalListParams(PaginationParams):
    signal_type: Optional[str] = None
    status: Optional[str] = None


class KBExternalBase(BaseSchema):
    url: Optional[str] = None
    title: Optional[str] = None
    source_platform: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    status: str = "fetched"
    fact_refs: List[int] = Field(default_factory=list)
    metadata_: dict = Field(default_factory=dict, alias="metadata")

    @model_validator(mode="before")
    @classmethod
    def _fix_orm(cls, data):
        return _orm_to_metadata_dict(data)


class KBExternalCreate(KBExternalBase):
    pass


class KBExternalUpdate(BaseSchema):
    url: Optional[str] = None
    title: Optional[str] = None
    source_platform: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[str] = None
    fact_refs: Optional[List[int]] = None
    metadata_: Optional[dict] = Field(default=None, alias="metadata")

    @model_validator(mode="before")
    @classmethod
    def _fix_orm(cls, data):
        return _orm_to_metadata_dict(data)


class KBExternalResponse(KBExternalBase, IDModel, TimestampResponse):
    enterprise_id: int
    last_fetched_at: Optional[datetime] = None


class KBExternalListParams(PaginationParams):
    source_platform: Optional[str] = None
    status: Optional[str] = None


class KBSummary(BaseSchema):
    facts: int = 0
    faqs: int = 0
    signals: int = 0
    externals: int = 0
    verified_facts: int = 0
    verified_faqs: int = 0
    last_updated: Optional[datetime] = None
