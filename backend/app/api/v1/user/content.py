from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, List

from pydantic import BaseModel

from app.core.config import settings
from app.core.db import get_db
from app.api.common import get_current_active_user, require_role
from app.models import User
from app.schemas.business import (
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioResponse,
    ScenarioListParams,
    ContentDraftCreate,
    ContentDraftUpdate,
    ContentDraftResponse,
    ContentDraftListParams,
    BulkApproveRequest,
    FactVerifyReport,
    ComplianceReport,
    ApprovalLogResponse,
)
from app.schemas.common import PaginatedResponse, ApiResponse
from app.service import ScenarioService, ContentService

router = APIRouter(prefix=f"{settings.API_V1_PREFIX}/user/content", tags=["用户端·舱2·内容"])


# ============ Scenario ============

@router.get("/scenarios", response_model=PaginatedResponse)
def list_scenarios(
    page: int = 1, page_size: int = 20,
    channel: Optional[str] = None, skill: Optional[str] = None, status: Optional[str] = None,
    keyword: str = "",
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    items, total = ScenarioService.list(
        db, user.enterprise_id,
        ScenarioListParams(page=page, page_size=page_size, channel=channel, skill=skill, status=status, keyword=keyword),
    )
    return {"code": 0, "message": "", "data": {
        "items": [ScenarioResponse.model_validate(ScenarioService._load(i)) for i in items],
        "total": total, "page": page, "page_size": page_size}}


@router.get("/scenarios/{sid}", response_model=ScenarioResponse)
def get_scenario(sid: int, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    s = ScenarioService.get(db, user.enterprise_id, sid)
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "场景不存在")
    return s


@router.post("/scenarios", response_model=ScenarioResponse)
@require_role(["owner", "admin", "editor", "member"])
def create_scenario(data: ScenarioCreate, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return ScenarioService.create(db, user.enterprise_id, data)


@router.put("/scenarios/{sid}", response_model=ScenarioResponse)
@require_role(["owner", "admin", "editor", "member"])
def update_scenario(sid: int, data: ScenarioUpdate, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        return ScenarioService.update(db, user.enterprise_id, sid, data)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.delete("/scenarios/{sid}", status_code=status.HTTP_204_NO_CONTENT)
@require_role(["owner", "admin", "editor"])
def delete_scenario(sid: int, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        ScenarioService.delete(db, user.enterprise_id, sid)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.post("/scenarios/{sid}/generate-drafts", response_model=PaginatedResponse, summary="生产子图：为 scenario 批量生成草稿")
@require_role(["owner", "admin", "editor"])
def generate_drafts(sid: int, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        items = ContentService.generate_drafts_for_scenario(db, user.enterprise_id, sid)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    from app.content_factory import draft_api_view

    return {"code": 0, "message": "ok", "data": {
        "items": [draft_api_view(ContentService._load(i)) for i in items],
        "total": len(items), "page": 1, "page_size": len(items)}}


# ============ Content Drafts ============

@router.get("/drafts", response_model=PaginatedResponse)
def list_drafts(
    page: int = 1, page_size: int = 20,
    scenario_id: Optional[int] = None, channel: Optional[str] = None,
    skill: Optional[str] = None, human_review_status: Optional[str] = None, status: Optional[str] = None,
    keyword: str = "",
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if settings.is_dev:
        from app.dev_seed import ensure_tenant_seed_data

        ensure_tenant_seed_data(db, user.enterprise_id, user.id)
    items, total = ContentService.list(
        db, user.enterprise_id,
        ContentDraftListParams(
            page=page, page_size=page_size, scenario_id=scenario_id,
            channel=channel, skill=skill, human_review_status=human_review_status, status=status,
            keyword=keyword,
        ),
    )
    from app.content_factory import draft_api_view

    return {"code": 0, "message": "ok", "data": {
        "items": [draft_api_view(ContentService._load(i)) for i in items],
        "total": total, "page": page, "page_size": page_size}}


@router.get("/drafts/{did}")
def get_draft(did: int, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    d = ContentService.get(db, user.enterprise_id, did)
    if not d:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "草稿不存在")
    from app.content_factory import draft_api_view

    return {"code": 0, "message": "ok", "data": draft_api_view(d)}


@router.post("/drafts", response_model=ContentDraftResponse)
@require_role(["owner", "admin", "editor", "member"])
def create_draft(data: ContentDraftCreate, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        return ContentService.create(db, user.enterprise_id, data)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.put("/drafts/{did}", response_model=ContentDraftResponse)
@require_role(["owner", "admin", "editor", "member"])
def update_draft(did: int, data: ContentDraftUpdate, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        return ContentService.update(db, user.enterprise_id, did, data)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.delete("/drafts/{did}", status_code=status.HTTP_204_NO_CONTENT)
@require_role(["owner", "admin", "editor"])
def delete_draft(did: int, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        ContentService.delete(db, user.enterprise_id, did)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


# ============ 审核（机器 + 人工）============

@router.post("/drafts/{did}/machine-review", summary="机器审：5 项检测链")
@require_role(["owner", "admin", "editor"])
def machine_review(did: int, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        item = ContentService.run_machine_review(db, user.enterprise_id, did)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    from app.content_factory import draft_api_view

    return {"code": 0, "message": "ok", "data": draft_api_view(item)}


@router.post("/drafts/{did}/fact-verify", response_model=FactVerifyReport, summary="fact_verify 单跑")
@require_role(["owner", "admin", "editor"])
def fact_verify(did: int, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        return ContentService.machine_verify_facts(db, user.enterprise_id, did)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.post("/drafts/{did}/compliance", response_model=ComplianceReport, summary="compliance 单跑")
@require_role(["owner", "admin", "editor"])
def compliance(did: int, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        return ContentService.machine_verify_compliance(db, user.enterprise_id, did)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


class RejectBody(BaseModel):
    reason: Optional[str] = None


@router.post("/drafts/{did}/approve", summary="人审通过（闸门）")
@require_role(["owner", "admin", "editor"])
def human_approve(
    did: int,
    note: Optional[str] = Query(None),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        item = ContentService.human_approve(db, user.enterprise_id, did, user.id, note)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    from app.content_factory import draft_api_view

    return {"code": 0, "message": "ok", "data": draft_api_view(item)}


@router.post("/drafts/{did}/reject", summary="人审驳回 → draft")
@require_role(["owner", "admin", "editor"])
def human_reject(
    did: int,
    body: Optional[RejectBody] = None,
    note: Optional[str] = Query(None),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    reason = (body.reason if body else None) or note
    try:
        item = ContentService.human_reject(db, user.enterprise_id, did, user.id, reason)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    from app.content_factory import draft_api_view

    return {"code": 0, "message": "ok", "data": {"id": item.id, "status": item.status, **draft_api_view(item)}}


@router.post("/drafts/bulk-approve", response_model=ApiResponse, summary="草稿批量审批")
@require_role(["owner", "admin", "editor"])
def bulk_approve(req: BulkApproveRequest, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ContentService.bulk_approve(db, user.enterprise_id, user.id, req)
    return {"code": 0, "message": f"已审批 {data.get('approved', 0)} 条", "data": data}


@router.get("/drafts/{did}/approval-logs", response_model=PaginatedResponse, summary="草稿审阅审计日志")
def list_approval_logs(
    did: int,
    page: int = 1,
    page_size: int = 20,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    from app.models import ApprovalLog

    q = db.query(ApprovalLog).filter(
        ApprovalLog.enterprise_id == user.enterprise_id,
        ApprovalLog.content_asset_id == did,
    )
    total = q.count()
    items = q.order_by(ApprovalLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "code": 0,
        "message": "",
        "data": {
            "items": [ApprovalLogResponse.model_validate(i) for i in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }
