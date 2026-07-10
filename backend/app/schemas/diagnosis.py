"""诊断 DTO — 对齐 models/strategy.py 中 SourceDiagnosis 产出。"""
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.schemas.common import BaseSchema


class PainPoint(BaseSchema):
    point: str
    severity: int = Field(5, ge=1, le=10)
    evidence: Optional[str] = None
    scenario_ids: List[int] = Field(default_factory=list)


class PersonaData(BaseSchema):
    age_range: List[int] = Field(default_factory=lambda: [25, 45])
    genders: List[str] = Field(default_factory=lambda: ["女性"])
    cities: List[str] = Field(default_factory=list)
    core_needs: List[str] = Field(default_factory=list)
    decision_factors: List[str] = Field(default_factory=list)
    typical_queries: List[str] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)


class CompetitorItem(BaseSchema):
    name: str
    type: str = "local"
    ai_mention_rate: int = Field(0, ge=0, le=100)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    differentiator: Optional[str] = None
