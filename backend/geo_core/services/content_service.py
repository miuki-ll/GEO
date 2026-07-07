from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
import re
import random

from sqlalchemy import or_
from sqlalchemy.orm import Session

from geo_core.core.logging_config import get_logger
from geo_core.models import ContentDraft, KBFact
from geo_core.schemas.business import (
    ContentDraftCreate,
    ContentDraftUpdate,
    ContentDraftListParams,
    BulkApproveRequest,
    FactVerifyReport,
    ComplianceReport,
)
from geo_core.utils.helpers import parse_list_from_str, to_list_str
from geo_core.services.scenario_service import ScenarioService
from geo_core.services.auth_service import EnterpriseService
from geo_core.services.kb_service import FactService
from geo_core.schemas.kb import KBFactListParams

logger = get_logger(__name__)

_FORBIDDEN_CN = ["最", "第一", "顶级", "国家级", "纯天然", "无任何副作用", "根治", "永不复发", "100%有效", "彻底解决"]


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
        fact_refs_val = None
        try:
            fact_refs_val = parse_list_from_str(getattr(it, "fact_refs", "[]") or "[]")
        except Exception:
            fact_refs_val = []
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
        payload["fact_refs"] = to_list_str(data.fact_refs)
        payload["fact_verify_report"] = data.fact_verify_report.model_dump() if data.fact_verify_report else {}
        payload["compliance_report"] = data.compliance_report.model_dump() if data.compliance_report else {}
        draft = ContentDraft(**payload)
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
            upd["fact_refs"] = to_list_str(upd["fact_refs"])
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
        report = FactVerifyReport(passed=True, hits=[], missing_refs=[], extra_text=None)
        fact_ids = [fid for fid in (draft.fact_refs or []) if isinstance(fid, int)]
        if fact_ids:
            facts = db.query(KBFact).filter(KBFact.enterprise_id == enterprise_id, KBFact.id.in_(fact_ids)).all()
            fact_map = {f.id: f for f in facts}
            for fid in fact_ids:
                f = fact_map.get(fid)
                if not f:
                    report.missing_refs.append(fid)
                    report.passed = False
                    continue
                claim = f.content or ""
                text = draft.content or ""
                hit = bool(claim) and any(
                    part in text for part in re.split(r"[，,。；;！!?？\s]", claim) if len(part) >= 3
                )
                report.hits.append({"fact_id": fid, "claim": claim, "hit": hit, "ref_citation_found": hit})
                if not hit:
                    report.passed = False
        return report

    @staticmethod
    def machine_verify_compliance(db: Session, enterprise_id: int, did: int) -> ComplianceReport:
        draft = ContentService.get(db, enterprise_id, did)
        if not draft:
            raise ValueError("草稿不存在")
        report = ComplianceReport(passed=True, issues=[], forbidden_words=[])
        text = f"{draft.title}\n{draft.content}"
        for w in _FORBIDDEN_CN:
            if w in text:
                report.forbidden_words.append(w)
                report.passed = False
                report.issues.append({"type": "forbidden", "word": w, "position": text.find(w)})
        return report

    @staticmethod
    def run_machine_review(db: Session, enterprise_id: int, did: int) -> ContentDraft:
        fact_report = ContentService.machine_verify_facts(db, enterprise_id, did)
        comp_report = ContentService.machine_verify_compliance(db, enterprise_id, did)
        machine_pass = fact_report.passed and comp_report.passed
        upd = ContentDraftUpdate(
            fact_verify_pass=fact_report.passed,
            fact_verify_report=fact_report,
            compliance_pass=comp_report.passed,
            compliance_report=comp_report,
            status="reviewed" if machine_pass else "blocked",
        )
        it = ContentService.get(db, enterprise_id, did)
        # manual field
        it.machine_review_pass = machine_pass
        db.commit()
        return ContentService.update(db, enterprise_id, did, upd)

    @staticmethod
    def human_approve(db: Session, enterprise_id: int, did: int, actor_id: int, note: Optional[str] = None) -> ContentDraft:
        draft = ContentService.get(db, enterprise_id, did)
        if not draft:
            raise ValueError("草稿不存在")
        upd = ContentDraftUpdate(
            human_review_status="approved",
            human_review_note=note,
            status="approved",
        )
        updated = ContentService.update(db, enterprise_id, did, upd)
        updated.human_review_by = actor_id
        updated.human_review_at = datetime.utcnow()
        db.commit()
        db.refresh(updated)
        return ContentService._load(updated)

    @staticmethod
    def human_reject(db: Session, enterprise_id: int, did: int, actor_id: int, note: Optional[str] = None) -> ContentDraft:
        upd = ContentDraftUpdate(
            human_review_status="rejected",
            human_review_note=note,
            status="needs_edit",
        )
        it = ContentService.update(db, enterprise_id, did, upd)
        it.human_review_by = actor_id
        it.human_review_at = datetime.utcnow()
        db.commit()
        db.refresh(it)
        return ContentService._load(it)

    @staticmethod
    def bulk_approve(db: Session, enterprise_id: int, actor_id: int, req: BulkApproveRequest) -> List[int]:
        ok_ids = []
        for did in req.ids:
            try:
                ContentService.human_approve(db, enterprise_id, did, actor_id, req.note)
                ok_ids.append(did)
            except Exception as e:
                logger.warning("bulk_approve skip id=%s err=%s", did, e)
        logger.info("bulk_approve done n=%d enterprise=%s", len(ok_ids), enterprise_id)
        return ok_ids

    @staticmethod
    def generate_drafts_for_scenario(
        db: Session, enterprise_id: int, scenario_id: int, persona: Optional[Dict[str, Any]] = None
    ) -> List[ContentDraft]:
        scenario = ScenarioService.get(db, enterprise_id, scenario_id)
        if not scenario:
            raise ValueError("Scenario 不存在")
        facts, _ = FactService.list(db, enterprise_id, KBFactListParams(page=1, page_size=10))
        facts_text = "\n".join([f"- [{f.id}] {f.content}" for f in facts])
        fact_ids = [f.id for f in facts[:5]]
        titles = [
            f"{scenario.title} · FAQ 标准问答",
            f"{scenario.title} · 深度种草稿",
            f"{scenario.title} · 场景对比稿",
        ]
        created = []
        for i, title in enumerate(titles):
            skill = "faq" if i == 0 else ("article" if i == 1 else "comparison")
            body = (
                f"根据以下已核验事实：\n{facts_text}\n\n"
                f"针对用户问题：{scenario.user_query}\n"
                f"输出内容：{title}。\n"
                "如需引用事实，使用 [fact_ref:#id] 标注；成分描述全部来自 KB；不使用医疗功效用语。"
            )
            draft = ContentDraftCreate(
                scenario_id=scenario.id,
                title=title,
                content=body,
                skill=skill,
                channel=scenario.channel or "hosted",
                fact_refs=fact_ids,
                status="draft",
                version=1,
            )
            created.append(ContentService.create(db, enterprise_id, draft))
        return created
