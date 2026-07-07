from typing import Optional, List, Any, Dict
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


# ============ Scenario ============
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
        return _orm_to_metadata_dict(data)


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
        return _orm_to_metadata_dict(data)


class ScenarioResponse(ScenarioBase, IDModel, TimestampResponse):
    enterprise_id: int


class ScenarioListParams(PaginationParams):
    channel: Optional[str] = None
    skill: Optional[str] = None
    status: Optional[str] = None


# ============ StrategyPack ============
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
        return _orm_to_metadata_dict(data)


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
        return _orm_to_metadata_dict(data)


class StrategyPackResponse(StrategyPackBase, IDModel, TimestampResponse):
    enterprise_id: int
    status: str
    confirmed_at: Optional[datetime] = None
    confirmed_by: Optional[int] = None


class StrategyPackListParams(PaginationParams):
    status: Optional[str] = None


# ============ ContentDraft ============
class FactVerifyReport(BaseSchema):
    passed: bool = False
    hits: List[Dict[str, Any]] = Field(default_factory=list)
    missing_refs: List[int] = Field(default_factory=list)
    extra_text: Optional[str] = None


class ComplianceReport(BaseSchema):
    passed: bool = False
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    forbidden_words: List[str] = Field(default_factory=list)


class ContentDraftBase(BaseSchema):
    scenario_id: int
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    skill: str = "faq"
    channel: str = "hosted"
    fact_refs: List[int] = Field(default_factory=list)
    fact_verify_pass: Optional[bool] = None
    fact_verify_report: FactVerifyReport = Field(default_factory=FactVerifyReport)
    compliance_pass: Optional[bool] = None
    compliance_report: ComplianceReport = Field(default_factory=ComplianceReport)
    human_review_status: str = "pending"
    human_review_note: Optional[str] = None
    status: str = "draft"
    version: int = 1


class ContentDraftCreate(ContentDraftBase):
    pass


class ContentDraftUpdate(BaseSchema):
    scenario_id: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None
    skill: Optional[str] = None
    channel: Optional[str] = None
    fact_refs: Optional[List[int]] = None
    fact_verify_pass: Optional[bool] = None
    fact_verify_report: Optional[FactVerifyReport] = None
    compliance_pass: Optional[bool] = None
    compliance_report: Optional[ComplianceReport] = None
    human_review_status: Optional[str] = None
    human_review_note: Optional[str] = None
    status: Optional[str] = None


class ContentDraftResponse(ContentDraftBase, IDModel, TimestampResponse):
    enterprise_id: int
    machine_review_pass: Optional[bool] = None
    human_review_by: Optional[int] = None
    human_review_at: Optional[datetime] = None


class ContentDraftListParams(PaginationParams):
    scenario_id: Optional[int] = None
    channel: Optional[str] = None
    skill: Optional[str] = None
    human_review_status: Optional[str] = None
    status: Optional[str] = None


class BulkApproveRequest(BaseSchema):
    ids: List[int]
    note: Optional[str] = None


# ============ PublishTask ============
class PublishTaskBase(BaseSchema):
    draft_id: int
    channel: str = "hosted"
    mode: str = "auto"
    target_url: Optional[str] = None
    metadata_: Dict[str, Any] = Field(default_factory=dict, alias="metadata")

    @model_validator(mode="before")
    @classmethod
    def _fix_orm(cls, data):
        return _orm_to_metadata_dict(data)


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
        return _orm_to_metadata_dict(data)


class PublishTaskResponse(PublishTaskBase, IDModel, TimestampResponse):
    enterprise_id: int
    status: str = "pending"
    retry_count: int = 0
    error_message: Optional[str] = None
    published_url: Optional[str] = None
    published_id: Optional[str] = None
    published_at: Optional[datetime] = None


class PublishTaskListParams(PaginationParams):
    draft_id: Optional[int] = None
    channel: Optional[str] = None
    mode: Optional[str] = None
    status: Optional[str] = None


# ============ MonitorResult ============
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
    run_at: Optional[datetime] = None
    batch_no: Optional[str] = None
    metadata_: Dict[str, Any] = Field(default_factory=dict, alias="metadata")

    @model_validator(mode="before")
    @classmethod
    def _fix_orm(cls, data):
        return _orm_to_metadata_dict(data)


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


# ============ AgentTask ============
class AgentTaskBase(BaseSchema):
    task_type: str
    graph_name: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)


class AgentTaskCreate(AgentTaskBase):
    pass


class AgentTaskUpdate(BaseSchema):
    status: Optional[str] = None
    progress_pct: Optional[int] = None
    progress_message: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AgentTaskResponse(AgentTaskBase, IDModel, TimestampResponse):
    enterprise_id: int
    celery_task_id: Optional[str] = None
    status: str = "pending"
    progress_pct: int = 0
    progress_message: Optional[str] = None
    output_data: Dict[str, Any] = Field(default_factory=dict)
    trace_id: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AgentTaskListParams(PaginationParams):
    task_type: Optional[str] = None
    status: Optional[str] = None


# ============ OutcomeSnapshot / Dashboard ============
class DashboardKpi(BaseSchema):
    total_scenarios: int = 0
    total_drafts_published: int = 0
    avg_mention_rate: float = 0.0
    avg_trust_score: float = 0.0
    core_queries: int = 0
    probe_discoveries: int = 0
    pending_review: int = 0
    kb_facts_verified: int = 0


class ChannelBreakdown(BaseSchema):
    channel: str
    published: int = 0
    mention_rate: float = 0.0
    avg_trust: float = 0.0


class EngineBreakdown(BaseSchema):
    engine: str
    mention_rate: float = 0.0
    avg_trust: float = 0.0
    sample_size: int = 0


class DashboardData(BaseSchema):
    period: str = "week"
    kpi: DashboardKpi = Field(default_factory=DashboardKpi)
    by_channel: List[ChannelBreakdown] = Field(default_factory=list)
    by_engine: List[EngineBreakdown] = Field(default_factory=list)
    trend: List[Dict[str, Any]] = Field(default_factory=list)
    alerts: List[Dict[str, Any]] = Field(default_factory=list)


class OutcomeSnapshotBase(BaseSchema):
    period: str = "week"
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    snapshot_type: str = "dashboard"
    metrics: Dict[str, Any] = Field(default_factory=dict)
    breakdown: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


class OutcomeSnapshotResponse(OutcomeSnapshotBase, IDModel, TimestampResponse):
    enterprise_id: int
