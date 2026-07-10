"""策略 / Scenario / 方案包 — 对齐 models/strategy.py。"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field, model_validator

from app.schemas.common import BaseSchema, IDModel, TimestampResponse, PaginationParams
from app.schemas._helpers import orm_to_metadata_dict
from app.schemas.diagnosis import PainPoint, PersonaData, CompetitorItem


class ScenarioBase(BaseSchema):
    title: str = Field(..., min_length=1, max_length=500)
    user_query: str = Field(..., min_length=1)
    intent: Optional[str] = None
    channel: str = "hosted"
    skill: str = "faq"
    priority: int = Field(5, ge=1, le=10)
    status: str = "draft"
    target_engines: List[str] = Field(default_factory=list)
    persona_ref: Dict[str, Any] = Field(default_factory=dict)
    competitor_ref: Dict[str, Any] = Field(default_factory=dict)
    fact_refs: List[int] = Field(default_factory=list)
    gap_analysis: Optional[str] = None
    metadata_: Dict[str, Any] = Field(default_factory=dict, alias="metadata")

    @model_validator(mode="before")
    @classmethod
    def _fix_orm(cls, data):
        return orm_to_metadata_dict(data)


class ScenarioCreate(ScenarioBase):
    pass


class ScenarioUpdate(BaseSchema):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    user_query: Optional[str] = None
    intent: Optional[str] = None
    channel: Optional[str] = None
    skill: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    status: Optional[str] = None
    target_engines: Optional[List[str]] = None
    persona_ref: Optional[Dict[str, Any]] = None
    competitor_ref: Optional[Dict[str, Any]] = None
    fact_refs: Optional[List[int]] = None
    gap_analysis: Optional[str] = None
    metadata_: Optional[Dict[str, Any]] = Field(default=None, alias="metadata")

    @model_validator(mode="before")
    @classmethod
    def _fix_orm(cls, data):
        return orm_to_metadata_dict(data)


class ScenarioResponse(ScenarioBase, IDModel, TimestampResponse):
    enterprise_id: int


class ScenarioListParams(PaginationParams):
    channel: Optional[str] = None
    skill: Optional[str] = None
    status: Optional[str] = None


class ChannelWeight(BaseSchema):
    name: str
    weight: int = Field(0, ge=0, le=100)
    mode: str = "auto"


class StrategyPackBase(BaseSchema):
    version: str = "1.0"
    persona: PersonaData = Field(default_factory=PersonaData)
    competitors: List[CompetitorItem] = Field(default_factory=list)
    pain_points: List[PainPoint] = Field(default_factory=list)
    scenarios: List[Dict[str, Any]] = Field(default_factory=list)
    channels: List[ChannelWeight] = Field(default_factory=list)
    weights: Dict[str, Any] = Field(default_factory=dict)
    metadata_: Dict[str, Any] = Field(default_factory=dict, alias="metadata")

    @model_validator(mode="before")
    @classmethod
    def _fix_orm(cls, data):
        return orm_to_metadata_dict(data)


class StrategyPackCreate(StrategyPackBase):
    pass


class StrategyPackUpdate(BaseSchema):
    version: Optional[str] = None
    persona: Optional[PersonaData] = None
    competitors: Optional[List[CompetitorItem]] = None
    pain_points: Optional[List[PainPoint]] = None
    scenarios: Optional[List[Dict[str, Any]]] = None
    channels: Optional[List[ChannelWeight]] = None
    weights: Optional[Dict[str, Any]] = None
    metadata_: Optional[Dict[str, Any]] = Field(default=None, alias="metadata")

    @model_validator(mode="before")
    @classmethod
    def _fix_orm(cls, data):
        return orm_to_metadata_dict(data)


class StrategyPackResponse(StrategyPackBase, IDModel, TimestampResponse):
    enterprise_id: int
    status: str
    confirmed_at: Optional[datetime] = None
    confirmed_by: Optional[int] = None


class StrategyPackListParams(PaginationParams):
    status: Optional[str] = None
