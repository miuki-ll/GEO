"""ORM 模型 — 与 schemas/ 按域一一对应。

| models/      | schemas/        |
|--------------|-----------------|
| auth.py      | auth.py         |
| kb.py        | kb.py           |
| strategy.py  | strategy.py + diagnosis.py + agent.py |
| content.py   | content.py      |
| publish.py   | publish.py      |
| monitor.py   | monitor.py + dashboard.py |
| audit.py     | content.py (ApprovalLog) |
| events.py    | —               |
| ops.py       | —               |
"""
from app.models.base import TimestampMixin, TenantMixin

from app.models.auth import Enterprise, User, RolePermission, Brand, Store, Service

from app.models.strategy import (
    TargetEngine,
    SourceDiagnosis,
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
