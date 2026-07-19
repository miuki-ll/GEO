"""诊断 DTO — SourceDiagnosis / SearchResult / 源地图。"""

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


class SearchCitation(BaseSchema):
    """联网搜索返回的单条引用。"""
    url: str = ""
    title: str = ""
    summary: str = ""
    site_name: str = ""
    publish_time: Optional[str] = None


class SearchResultCreate(BaseSchema):
    """写入 search_results 表。"""
    probe_query: str = Field(..., min_length=1, max_length=500)
    engine: str
    answer: str = ""
    citations: List[SearchCitation] = Field(default_factory=list)
    citation_count: int = 0
    diagnosis_batch_no: Optional[str] = None
    latency_ms: int = 0
    error: Optional[str] = None


class SearchResultResponse(SearchResultCreate):
    """读取 search_results 表。"""
    id: int
    enterprise_id: int
    created_at: Optional[str] = None


class SourceMapItem(BaseSchema):
    """单个信源平台的统计。"""
    domain: str  # 如 "大众点评"、"小红书"
    site_name: str
    count: int
    weight: float = 0.0  # 占总引用的比例
    rankings: List[str] = Field(default_factory=list)  # 该平台上的排名靠前品牌
    gaps: List[str] = Field(default_factory=list)  # 我们的差距


class SourceMap(BaseSchema):
    """信源地图 — 各平台引用分布。"""
    total_citations: int = 0
    total_probes: int = 0
    platforms: List[SourceMapItem] = Field(default_factory=list)
    top_domains: List[str] = Field(default_factory=list)


class DiagnosisFullResponse(BaseSchema):
    """五区诊断完整响应。"""
    batch_no: str
    enterprise_id: int
    probes: List[str] = Field(default_factory=list)
    search_results: List[SearchResultResponse] = Field(default_factory=list)
    source_map: Optional[SourceMap] = None
    pain_points: List[PainPoint] = Field(default_factory=list)
    persona: Optional[PersonaData] = None
    competitors: List[CompetitorItem] = Field(default_factory=list)
    t0_written: bool = False
    created_at: Optional[str] = None
