"""B6 监测服务：Core/Probe profile · T1 写入 · Δ（假 T0 WAIT_FOR A7）。"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import random
import string

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.models import Enterprise, MonitorProfile, MonitorResult
from app.schemas.business import MonitorResultListParams, MonitorTriggerRequest
from app.service.auth_service import EnterpriseService
from app.monitor_delta import (
    DEFAULT_ENGINES,
    build_core_prompts,
    build_probe_prompts,
    compute_delta,
    normalize_engines,
    result_api_view,
)

logger = get_logger(__name__)


def _rand_id(n: int = 12) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


class MonitorService:
    @staticmethod
    def resolve_engines(db: Session, enterprise_id: int) -> List[str]:
        ent = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
        raw = None
        if ent is not None:
            settings = getattr(ent, "settings", None) or {}
            if isinstance(settings, dict):
                raw = settings.get("target_engines")
            # 兼容：部分种子把 engines 放 settings；handoff 在 enterprise JSON
        if not raw:
            try:
                from app.channel_weights import load_handoff_mock

                raw = (load_handoff_mock().get("enterprise") or {}).get("target_engines")
            except Exception:
                raw = None
        return normalize_engines(raw)

    @staticmethod
    def ensure_profile(db: Session, enterprise_id: int) -> MonitorProfile:
        existing = (
            db.query(MonitorProfile)
            .filter(MonitorProfile.enterprise_id == enterprise_id, MonitorProfile.is_active.is_(True))
            .order_by(MonitorProfile.id.desc())
            .first()
        )
        if existing:
            # 跟随最新 target_engines
            engines = MonitorService.resolve_engines(db, enterprise_id)
            if list(existing.target_engines or []) != engines:
                existing.target_engines = engines
                existing.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(existing)
            return existing

        from app.channel_weights import load_handoff_mock

        handoff = load_handoff_mock()
        core = build_core_prompts(handoff, limit=20)
        if not core:
            core = ["静安寺皮肤管理推荐", "敏感肌能不能做皮肤管理"]
        probe = build_probe_prompts(core, limit=10)
        engines = MonitorService.resolve_engines(db, enterprise_id)
        profile = MonitorProfile(
            enterprise_id=enterprise_id,
            name="default",
            target_engines=engines,
            core_prompts=core,
            probe_prompts=probe,
            thresholds={"mention_warn": 0.5},
            is_active=True,
            metadata_={"source": "b6_ensure_profile"},
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        logger.info("MonitorProfile created id=%s enterprise=%s engines=%s", profile.id, enterprise_id, engines)
        return profile

    @staticmethod
    def profile_view(profile: MonitorProfile) -> Dict[str, Any]:
        return {
            "id": profile.id,
            "name": profile.name,
            "target_engines": list(profile.target_engines or []),
            "core_prompts": list(profile.core_prompts or [])[:20],
            "probe_prompts": list(profile.probe_prompts or [])[:10],
            "core_count": len(profile.core_prompts or []),
            "probe_count": len(profile.probe_prompts or []),
            "thresholds": profile.thresholds or {},
            "is_active": bool(profile.is_active),
        }

    @staticmethod
    def seed_mock_t0(db: Session, enterprise_id: int) -> Dict[str, Any]:
        """开发态假 T0。TODO(WAIT_FOR: A7) 真诊断写入。"""
        existing = (
            db.query(MonitorResult)
            .filter(MonitorResult.enterprise_id == enterprise_id, MonitorResult.baseline.is_(True))
            .count()
        )
        if existing:
            return {"created": 0, "skipped": existing, "todo": "WAIT_FOR: A7"}

        from app.channel_weights import load_handoff_mock

        handoff = load_handoff_mock()
        samples = ((handoff.get("t0_baseline") or {}).get("sample_t0_records")) or []
        profile = MonitorService.ensure_profile(db, enterprise_id)
        batch_no = f"t0-mock-{enterprise_id}-{_rand_id(4)}"
        created = 0
        if not samples:
            # 最小假 T0：core 前 2 条 × 引擎
            for eng in list(profile.target_engines or DEFAULT_ENGINES)[:2]:
                for q in list(profile.core_prompts or [])[:2]:
                    db.add(
                        MonitorResult(
                            enterprise_id=enterprise_id,
                            profile_id=profile.id,
                            pool_type="core",
                            engine=eng,
                            query=q,
                            mentioned=False,
                            baseline=True,
                            run_at=datetime.utcnow(),
                            batch_no=batch_no,
                            metrics={"hallucination": False, "citations": [], "mock_t0": True},
                            metadata_={"todo": "WAIT_FOR: A7"},
                        )
                    )
                    created += 1
        else:
            for s in samples:
                eng = (s.get("engine_code") or "doubao")
                db.add(
                    MonitorResult(
                        enterprise_id=enterprise_id,
                        profile_id=profile.id,
                        pool_type="core",
                        engine=eng,
                        query=s.get("prompt") or "静安寺皮肤管理推荐",
                        mentioned=bool(s.get("brand_mentioned")),
                        position_rank=s.get("rank"),
                        baseline=True,
                        run_at=datetime.utcnow(),
                        batch_no=batch_no,
                        metrics={
                            "hallucination": bool(s.get("hallucination")),
                            "citations": list(s.get("citations") or []),
                            "mock_t0": True,
                        },
                        metadata_={"todo": "WAIT_FOR: A7"},
                    )
                )
                created += 1
        db.commit()
        return {"created": created, "batch_no": batch_no, "todo": "WAIT_FOR: A7"}

    @staticmethod
    def list(db: Session, enterprise_id: int, params: MonitorResultListParams) -> Tuple[List[MonitorResult], int]:
        q = db.query(MonitorResult).filter(MonitorResult.enterprise_id == enterprise_id)
        if params.pool_type:
            q = q.filter(MonitorResult.pool_type == params.pool_type)
        if params.engine:
            q = q.filter(MonitorResult.engine == params.engine)
        if params.scenario_id:
            q = q.filter(MonitorResult.scenario_id == params.scenario_id)
        if params.batch_no:
            q = q.filter(MonitorResult.batch_no == params.batch_no)
        baseline = getattr(params, "baseline", None)
        if baseline is not None:
            q = q.filter(MonitorResult.baseline.is_(bool(baseline)))
        total = q.count()
        items = (
            q.order_by(MonitorResult.created_at.desc())
            .offset((params.page - 1) * params.page_size)
            .limit(params.page_size)
            .all()
        )
        return items, total

    @staticmethod
    def trigger(db: Session, enterprise_id: int, req: MonitorTriggerRequest) -> Dict[str, Any]:
        """写入 T1（baseline=false）。引擎跟随 profile / enterprise.target_engines。"""
        profile = MonitorService.ensure_profile(db, enterprise_id)
        engines = list(profile.target_engines or []) or MonitorService.resolve_engines(db, enterprise_id)
        prompts = list(profile.core_prompts or []) if req.pool == "core" else list(profile.probe_prompts or [])
        if not prompts:
            prompts = ["敏感肌推荐哪家美容院"]
        # Core ~20 / Probe ≤10 硬限
        prompts = prompts[:20] if req.pool == "core" else prompts[:10]

        batch_no = f"t1-{req.pool}-{enterprise_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{_rand_id(4)}"
        created_count = 0
        for qtext in prompts:
            for eng in engines:
                mentioned = random.random() < (0.55 if req.pool == "core" else 0.35)
                mr = MonitorResult(
                    enterprise_id=enterprise_id,
                    profile_id=profile.id,
                    pool_type=req.pool,
                    engine=eng,
                    scenario_id=(req.scenario_ids[0] if req.scenario_ids else None),
                    query=qtext,
                    mentioned=mentioned,
                    mention_snippet=("示例提及：" + qtext[:20]) if mentioned else None,
                    trust_score=round(0.4 + random.random() * 0.55, 3) if mentioned else round(random.random() * 0.3, 3),
                    position_rank=random.randint(1, 8) if mentioned else None,
                    baseline=False,  # T1
                    run_at=datetime.utcnow(),
                    batch_no=batch_no,
                    competitor_mentions=[],
                    metrics={"hallucination": False, "citations": [], "mock": True},
                    metadata_={"phase": "T1"},
                )
                db.add(mr)
                created_count += 1
        db.commit()
        EnterpriseService.touch_kb(db, enterprise_id)
        logger.info("MonitorService T1 trigger pool=%s n=%d batch=%s", req.pool, created_count, batch_no)
        return {
            "batch_no": batch_no,
            "created": created_count,
            "pool": req.pool,
            "baseline": False,
            "engines": engines,
            "prompt_count": len(prompts),
        }

    @staticmethod
    def delta(db: Session, enterprise_id: int, pool: str = "core") -> Dict[str, Any]:
        t0 = (
            db.query(MonitorResult)
            .filter(
                MonitorResult.enterprise_id == enterprise_id,
                MonitorResult.pool_type == pool,
                MonitorResult.baseline.is_(True),
            )
            .all()
        )
        t1 = (
            db.query(MonitorResult)
            .filter(
                MonitorResult.enterprise_id == enterprise_id,
                MonitorResult.pool_type == pool,
                MonitorResult.baseline.is_(False),
            )
            .all()
        )
        out = compute_delta(t0, t1)
        out["pool"] = pool
        return out

    @staticmethod
    def latest_trend(db: Session, enterprise_id: int, pool: str = "core", days: int = 7) -> List[Dict[str, Any]]:
        results = (
            db.query(MonitorResult)
            .filter(
                MonitorResult.enterprise_id == enterprise_id,
                MonitorResult.pool_type == pool,
                MonitorResult.created_at >= datetime.utcnow() - timedelta(days=days),
            )
            .order_by(MonitorResult.created_at.asc())
            .all()
        )
        by_day: Dict[str, List[MonitorResult]] = {}
        for r in results:
            key = r.created_at.strftime("%Y-%m-%d")
            by_day.setdefault(key, []).append(r)
        out = []
        for day in sorted(by_day.keys()):
            rs = by_day[day]
            total = len(rs)
            m = sum(1 for r in rs if r.mentioned)
            avg_trust = round(sum(r.trust_score or 0 for r in rs) / total, 3) if total else 0.0
            out.append(
                {
                    "date": day,
                    "samples": total,
                    "mention_rate": round(m / total, 3) if total else 0.0,
                    "avg_trust": avg_trust,
                }
            )
        return out

    @staticmethod
    def result_view(row: MonitorResult) -> Dict[str, Any]:
        return result_api_view(row)
