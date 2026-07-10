"""内容草稿 / 审核 — 对齐 models/content.py + models/audit.py。"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.schemas.common import BaseSchema, IDModel, TimestampResponse, PaginationParams


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


class ApprovalLogResponse(IDModel, TimestampResponse):
    enterprise_id: int
    content_asset_id: int
    action: str
    actor_id: Optional[int] = None
    note: Optional[str] = None
    machine_review_snapshot: Dict[str, Any] = Field(default_factory=dict)
