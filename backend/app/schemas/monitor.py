"""监测结果 — 对齐 models/monitor.py。"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field, model_validator

from app.schemas.common import BaseSchema, IDModel, TimestampResponse, PaginationParams
from app.schemas._helpers import orm_to_metadata_dict


class MonitorResultBase(BaseSchema):
    pool_type: str = "core"
    engine: str
    query: str
    scenario_id: Optional[int] = None
    mentioned: bool = False
    mention_snippet: Optional[str] = None
    trust_score: Optional[float] = None
    position_rank: Optional[int] = None
    response_text: Optional[str] = None
    competitor_mentions: List[Dict[str, Any]] = Field(default_factory=list)
    baseline: bool = False  # True=T0 · False=T1（手册 B6）
    run_at: Optional[datetime] = None
    batch_no: Optional[str] = None
    metadata_: Dict[str, Any] = Field(default_factory=dict, alias="metadata")

    @model_validator(mode="before")
    @classmethod
    def _fix_orm(cls, data):
        return orm_to_metadata_dict(data)


class MonitorResultCreate(MonitorResultBase):
    pass


class MonitorResultResponse(MonitorResultBase, IDModel, TimestampResponse):
    enterprise_id: int


class MonitorResultListParams(PaginationParams):
    pool_type: Optional[str] = None
    engine: Optional[str] = None
    scenario_id: Optional[int] = None
    batch_no: Optional[str] = None


class MonitorTriggerRequest(BaseSchema):
    pool: str = "core"
    scenario_ids: List[int] = Field(default_factory=list)
