"""ORM 模型包 — 与 schemas/ 按域对应。"""

from app.models.base import TimestampMixin, TenantMixin

from app.models.auth import Enterprise, User, RolePermission, Brand, Store, Service

from app.models.strategy import (
    TargetEngine,
    SourceDiagnosis,
    SearchResult,
    Keyword,
    Scenario,
    StrategyPackDraft,
    StrategyPack,
    AgentTask,
)

from app.models.content import ContentAsset, ContentDraft

from app.models.publish import PublishTask

from app.models.monitor import MonitorProfile, MonitorResult, OutcomeSnapshot

from app.models.kb import KBFact, KBFaq, KBSignal, KBExternal

from app.models.audit import ApprovalLog, AgentTrace

from app.models.events import HostedPageEvent

from app.models.ops import FaissIndex

__all__ = [
    "TimestampMixin",
    "TenantMixin",
    "Enterprise",
    "User",
    "RolePermission",
    "Brand",
    "Store",
    "Service",
    "KBFact",
    "KBFaq",
    "KBSignal",
    "KBExternal",
    "TargetEngine",
    "SourceDiagnosis",
    "SearchResult",
    "Keyword",
    "Scenario",
    "StrategyPackDraft",
    "StrategyPack",
    "ContentAsset",
    "ContentDraft",
    "PublishTask",
    "MonitorProfile",
    "MonitorResult",
    "AgentTask",
    "OutcomeSnapshot",
    "ApprovalLog",
    "AgentTrace",
    "HostedPageEvent",
    "FaissIndex",
]
