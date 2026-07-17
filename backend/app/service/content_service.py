from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
import re
import random

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.models import ContentAsset, ContentDraft, KBFact, ApprovalLog
from app.schemas.business import (
    ContentDraftCreate,
    ContentDraftUpdate,
    ContentDraftListParams,
    BulkApproveRequest,
    FactVerifyReport,
    ComplianceReport,
)
from app.utils.helpers import ensure_json_list
from app.service.scenario_service import ScenarioService
from app.service.auth_service import EnterpriseService
from app.service.kb_service import FactService
from app.schemas.kb import KBFactListParams

logger = get_logger(__name__)

APPROVAL_TARGET_TYPE = "strategy_pack+content"


def _write_approval_log(
    db: Session,
    enterprise_id: int,
    content_asset_id: int,
    action: str,
    actor_id: int,
    note: Optional[str] = None,
    machine_review_snapshot: Optional[Dict[str, Any]] = None,
) -> ApprovalLog:
    log = ApprovalLog(
        enterprise_id=enterprise_id,
        content_asset_id=content_asset_id,
        action=action,
        actor_id=actor_id,
        note=note,
        machine_review_snapshot=machine_review_snapshot or {},
        metadata_={"target_type": APPROVAL_TARGET_TYPE},
    )
    db.add(log)
    return log


class ContentService:
    @staticmethod
    def list(db: Session, enterprise_id: int, params: ContentDraftListParams) -> Tuple[List[ContentDraft], int]:
        q = db.query(ContentDraft).filter(ContentDraft.enterprise_id == enterprise_id)
        if params.scenario_id:
            q = q.filter(ContentDraft.scenario_id == params.scenario_id)
        if params.channel:
            q = q.filter(ContentDraft.channel == params.channel)
        if params.skill:
            q = q.filter(ContentDraft.skill == params.skill)
        if params.human_review_status:
            q = q.filter(ContentDraft.human_review_status == params.human_review_status)
        if params.status:
            q = q.filter(ContentDraft.status == params.status)
        if params.keyword:
            kw = f"%{params.keyword}%"
            q = q.filter(or_(ContentDraft.title.ilike(kw), ContentDraft.content.ilike(kw)))
        total = q.count()
        items = (
            q.order_by(ContentDraft.updated_at.desc())
            .offset((params.page - 1) * params.page_size)
            .limit(params.page_size)
            .all()
        )
        for it in items:
            ContentService._load(it)
        return items, total

    @staticmethod
    def get(db: Session, enterprise_id: int, did: int) -> Optional[ContentDraft]:
        it = (
            db.query(ContentDraft)
            .filter(ContentDraft.id == did, ContentDraft.enterprise_id == enterprise_id)
            .first()
        )
        return ContentService._load(it) if it else None

    @staticmethod
    def _load(it: ContentDraft) -> ContentDraft:
        if not it:
            return it
        fact_refs_val = ensure_json_list(getattr(it, "fact_refs", []))
        if fact_refs_val is not None and hasattr(it, "fact_refs"):
            try:
                it.__dict__["fact_refs"] = fact_refs_val
            except Exception:
                object.__setattr__(it, "fact_refs", fact_refs_val)
        return it

    @staticmethod
    def create(db: Session, enterprise_id: int, data: ContentDraftCreate) -> ContentDraft:
        scenario = ScenarioService.get(db, enterprise_id, data.scenario_id)
        if not scenario:
            raise ValueError("Scenario 不存在")
        payload = data.model_dump(exclude={"fact_refs", "fact_verify_report", "compliance_report"}, by_alias=True)
        payload["enterprise_id"] = enterprise_id
        payload["fact_refs"] = list(data.fact_refs or [])
        payload["fact_verify_report"] = data.fact_verify_report.model_dump() if data.fact_verify_report else {}
        payload["compliance_report"] = data.compliance_report.model_dump() if data.compliance_report else {}
        draft = ContentAsset(**payload)
        db.add(draft)
        db.commit()
        db.refresh(draft)
        EnterpriseService.touch_kb(db, enterprise_id)
        logger.info("ContentDraft created id=%s enterprise=%s", draft.id, enterprise_id)
        return ContentService._load(draft)

    @staticmethod
    def update(db: Session, enterprise_id: int, did: int, data: ContentDraftUpdate) -> ContentDraft:
        it = ContentService.get(db, enterprise_id, did)
        if not it:
            raise ValueError("草稿不存在")
        upd = data.model_dump(exclude_unset=True, by_alias=True)
        if "fact_refs" in upd and upd["fact_refs"] is not None:
            upd["fact_refs"] = list(upd["fact_refs"])
        if "fact_verify_report" in upd and upd["fact_verify_report"] is not None:
            upd["fact_verify_report"] = upd["fact_verify_report"].model_dump() if hasattr(upd["fact_verify_report"], "model_dump") else upd["fact_verify_report"]
        if "compliance_report" in upd and upd["compliance_report"] is not None:
            upd["compliance_report"] = upd["compliance_report"].model_dump() if hasattr(upd["compliance_report"], "model_dump") else upd["compliance_report"]
        for k, v in upd.items():
            setattr(it, k, v)
        it.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(it)
        return ContentService._load(it)

    @staticmethod
    def delete(db: Session, enterprise_id: int, did: int) -> None:
        it = ContentService.get(db, enterprise_id, did)
        if not it:
            raise ValueError("草稿不存在")
        db.delete(it)
        db.commit()

    @staticmethod
    def machine_verify_facts(db: Session, enterprise_id: int, did: int) -> FactVerifyReport:
        draft = ContentService.get(db, enterprise_id, did)
        if not draft:
            raise ValueError("草稿不存在")
        from app.content_review import check_fact_verify

        fact_ids = [fid for fid in (draft.fact_refs or []) if isinstance(fid, int)]
        facts_rows = []
        if fact_ids:
            facts_rows = (
                db.query(KBFact)
                .filter(KBFact.enterprise_id == enterprise_id, KBFact.id.in_(fact_ids))
                .all()
            )
        facts = [
            {"id": f.id, "title": f.title, "content": f.content, "category": getattr(f, "category", "")}
            for f in facts_rows
        ]
        if not facts:
            from app.content_factory import kb_fetch

            facts = kb_fetch(fact_ids=fact_ids or None)
        result = check_fact_verify(draft.content or "", facts)
        report = FactVerifyReport(
            passed=bool(result["ok"]),
            hits=result.get("hits") or [],
            missing_refs=result.get("missing_refs") or [],
        )
        return report

    @staticmethod
    def machine_verify_compliance(db: Session, enterprise_id: int, did: int) -> ComplianceReport:
        draft = ContentService.get(db, enterprise_id, did)
        if not draft:
            raise ValueError("草稿不存在")
        from app.content_review import check_forbidden_words, resolve_forbidden_words
        from app.models import Enterprise

        ent = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
        pack_code = (getattr(ent, "industry_pack", None) if ent else None) or "beauty_local"
        words, _ = resolve_forbidden_words(pack_code)
        text = f"{draft.title}\n{draft.content}"
        result = check_forbidden_words(text, words)
        report = ComplianceReport(
            passed=bool(result["ok"]),
            issues=[{"type": "forbidden", "word": w} for w in (result.get("hits") or [])],
            forbidden_words=list(result.get("hits") or []),
        )
        return report

    @staticmethod
    def run_machine_review(db: Session, enterprise_id: int, did: int) -> ContentDraft:
        from app.content_review import run_five_machine_reviews
        from app.content_factory import kb_fetch
        from app.models import Enterprise

        draft = ContentService.get(db, enterprise_id, did)
        if not draft:
            raise ValueError("草稿不存在")

        fact_ids = [fid for fid in (draft.fact_refs or []) if isinstance(fid, int)]
        facts_rows = []
        if fact_ids:
            facts_rows = (
                db.query(KBFact)
                .filter(KBFact.enterprise_id == enterprise_id, KBFact.id.in_(fact_ids))
                .all()
            )
        facts = [
            {"id": f.id, "title": f.title, "content": f.content, "category": getattr(f, "category", "")}
            for f in facts_rows
        ] or kb_fetch(fact_ids=fact_ids or None)

        meta = dict(getattr(draft, "metadata_", None) or {})
        rag_slices = list(meta.get("rag_slices") or [])
        ent = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
        pack_code = (getattr(ent, "industry_pack", None) if ent else None) or "beauty_local"

        review = run_five_machine_reviews(
            body=draft.content or "",
            title=draft.title or "",
            facts=facts,
            rag_slices=rag_slices,
            industry_pack_code=pack_code,
        )
        mr = review["machine_review"]
        meta["machine_review"] = mr
        meta["machine_review_details"] = review["details"]
        draft.metadata_ = meta
        draft.fact_verify_pass = bool(mr.get("fact_verify"))
        draft.compliance_pass = bool(mr.get("forbidden_words"))
        draft.machine_review_pass = bool(review["passed"])
        draft.status = "ready" if review["passed"] else "draft"
        draft.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(draft)
        return ContentService._load(draft)

    @staticmethod
    def human_approve(db: Session, enterprise_id: int, did: int, actor_id: int, note: Optional[str] = None) -> ContentDraft:
        draft = ContentService.get(db, enterprise_id, did)
        if not draft:
            raise ValueError("草稿不存在")
        meta = dict(getattr(draft, "metadata_", None) or {})
        snapshot = meta.get("machine_review") or {
            "fact_verify": bool(draft.fact_verify_pass),
            "forbidden_words": bool(draft.compliance_pass),
            "cross_validation": True,
            "entity_consistency": True,
            "rag_readability": bool(meta.get("rag_slices")),
        }
        upd = ContentDraftUpdate(
            human_review_status="approved",
            human_review_note=note,
            status="approved",
        )
        updated = ContentService.update(db, enterprise_id, did, upd)
        updated.human_review_by = actor_id
        updated.human_review_at = datetime.utcnow()
        _write_approval_log(
            db,
            enterprise_id,
            did,
            "confirm",
            actor_id,
            note,
            machine_review_snapshot=snapshot,
        )
        db.commit()
        db.refresh(updated)
        try:
            from app.service.publish_service import PublishService

            PublishService.ensure_task_for_asset(db, enterprise_id, did)
        except Exception as e:
            logger.warning("ensure publish task after approve failed id=%s: %s", did, e)
        return ContentService._load(updated)

    @staticmethod
    def human_reject(db: Session, enterprise_id: int, did: int, actor_id: int, note: Optional[str] = None) -> ContentDraft:
        """驳回 → status=draft（手册 B4）。"""
        upd = ContentDraftUpdate(
            human_review_status="rejected",
            human_review_note=note,
            status="draft",
        )
        it = ContentService.update(db, enterprise_id, did, upd)
        it.human_review_by = actor_id
        it.human_review_at = datetime.utcnow()
        meta = dict(getattr(it, "metadata_", None) or {})
        _write_approval_log(
            db,
            enterprise_id,
            did,
            "reject",
            actor_id,
            note,
            machine_review_snapshot=meta.get("machine_review") or {},
        )
        db.commit()
        db.refresh(it)
        return ContentService._load(it)

    @staticmethod
    def bulk_approve(db: Session, enterprise_id: int, actor_id: int, req: BulkApproveRequest) -> Dict[str, Any]:
        ok_ids: List[int] = []
        failed: List[Dict[str, Any]] = []
        for did in req.ids:
            try:
                ContentService.human_approve(db, enterprise_id, did, actor_id, req.note)
                ok_ids.append(did)
            except Exception as e:
                logger.warning("bulk_approve skip id=%s err=%s", did, e)
                failed.append({"id": did, "error": str(e)})
        logger.info("bulk_approve done n=%d enterprise=%s", len(ok_ids), enterprise_id)
        return {
            "approved": len(ok_ids),
            "approved_ids": ok_ids,
            "failed": failed,
            "next_route": "/publish/tasks",
            "target_type": APPROVAL_TARGET_TYPE,
        }

    @staticmethod
    def generate_drafts_for_scenario(
        db: Session, enterprise_id: int, scenario_id: int, persona: Optional[Dict[str, Any]] = None
    ) -> List[ContentDraft]:
        """B3：固定链生成 1 scenario × channel × skill（可扩展多 skill）。"""
        from app.content_factory import run_fixed_chain

        scenario = ScenarioService.get(db, enterprise_id, scenario_id)
        if not scenario:
            raise ValueError("Scenario 不存在")

        facts, _ = FactService.list(db, enterprise_id, KBFactListParams(page=1, page_size=20))
        channel = scenario.channel or "hosted"
        skill = scenario.skill or "faq"
        produced = run_fixed_chain(
            user_query=scenario.user_query or scenario.title or "",
            channel=channel,
            skill=skill,
            db_facts=facts,
        )
        draft = ContentDraftCreate(
            scenario_id=scenario.id,
            title=produced["title"],
            content=produced["body"],
            skill=skill,
            channel=channel,
            fact_refs=produced["fact_refs"],
            status=produced.get("status") or "ready",
            version=1,
        )
        created = ContentService.create(db, enterprise_id, draft)
        meta = dict(getattr(created, "metadata_", None) or {})
        meta["rag_slices"] = produced["rag_slices"]
        meta["seven_segments"] = produced["seven_segments"]
        meta["machine_review"] = produced["machine_review"]
        meta["content_factory"] = {"mock": True, "todo": "WAIT_FOR: A2+A3"}
        created.metadata_ = meta
        db.commit()
        db.refresh(created)
        # B4：生成后跑 5 项机审
        reviewed = ContentService.run_machine_review(db, enterprise_id, created.id)
        return [reviewed]

    @staticmethod
    def generate_for_unit(
        db: Session,
        enterprise_id: int,
        *,
        scenario_id: int,
        user_query: str,
        channel: str,
        skill: str,
    ) -> ContentDraft:
        """confirm 路径：按 content_unit 生成一条草稿。"""
        from app.content_factory import run_fixed_chain

        facts, _ = FactService.list(db, enterprise_id, KBFactListParams(page=1, page_size=20))
        produced = run_fixed_chain(
            user_query=user_query,
            channel=channel or "hosted",
            skill=skill or "faq",
            db_facts=facts,
        )
        draft = ContentDraftCreate(
            scenario_id=scenario_id,
            title=produced["title"],
            content=produced["body"],
            skill=skill or "faq",
            channel=channel or "hosted",
            fact_refs=produced["fact_refs"],
            status=produced.get("status") or "ready",
            version=1,
        )
        created = ContentService.create(db, enterprise_id, draft)
        meta = dict(getattr(created, "metadata_", None) or {})
        meta["rag_slices"] = produced["rag_slices"]
        meta["seven_segments"] = produced["seven_segments"]
        meta["machine_review"] = produced["machine_review"]
        meta["content_factory"] = {"mock": True, "todo": "WAIT_FOR: A2+A3"}
        created.metadata_ = meta
        db.commit()
        db.refresh(created)
        return ContentService.run_machine_review(db, enterprise_id, created.id)
