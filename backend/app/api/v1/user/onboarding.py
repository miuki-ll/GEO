"""用户端 — 入驻引导运行、状态、SSE、快照。"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.logging_config import get_logger
from app.api.common import get_current_active_user
from app.models import User
from app.schemas.business import (
    AgentTaskResponse,
    DashboardData,
    AgentTaskCreate,
)
from app.schemas.onboarding import OnboardingRunRequest
from app.service import (
    StrategyPackService,
    ScenarioService,
    AgentTaskService,
    EnterpriseService,
)

logger = get_logger(__name__)

router = APIRouter(prefix=f"{settings.API_V1_PREFIX}/user/onboarding", tags=["用户端·舱1·开店向导"])


@router.post("/run", response_model=AgentTaskResponse, summary="触发开店向导：入驻表单 → LLM graph → 副作用写入")
def onboarding_run(
    body: OnboardingRunRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # 1. 创建 AgentTask
    task = AgentTaskService.create(
        db,
        user.enterprise_id,
        AgentTaskCreate(
            task_type="onboarding_pipeline",
            graph_name="onboarding",
            input_data=body.model_dump(),
        ),
    )

    # 2. 后台执行（async：runner.run_graph 为协程）
    async def _bg():
        from app.core.db import SessionLocal
        from app.agents.runner import run_graph

        s = SessionLocal()
        try:
            # 2a. 跑 graph（LLM 入驻流程）
            state = await run_graph(
                db=s,
                enterprise_id=user.enterprise_id,
                graph_name="onboarding",
                input_data=body.model_dump(),
                task_id=task.id,
            )

            # 2b. 副作用写入（A5-2：Brand/Store/Service/TargetEngine）
            _write_side_effects(s, user.enterprise_id, body)

            # 2c. KB 自动建库 + llms.txt（A5-3）
            _bootstrap_kb(s, user.enterprise_id, body, state)

            # 2d. touch kb
            EnterpriseService.touch_kb(s, user.enterprise_id)

        except Exception as e:
            AgentTaskService.complete_task(
                s, user.enterprise_id, task.id,
                output_data={}, error=str(e),
            )
        finally:
            s.close()

    background_tasks.add_task(_bg)
    return task


def _write_side_effects(db, enterprise_id: int, body: OnboardingRunRequest):
    """写入入驻副作用：Brand / Store / Service / TargetEngine。"""
    from app.models.auth import Brand, Store, Service
    from app.models.strategy import TargetEngine

    # Brand
    if body.brand:
        existing = db.query(Brand).filter(Brand.enterprise_id == enterprise_id).first()
        if not existing:
            db.add(Brand(
                enterprise_id=enterprise_id,
                name=body.brand.name,
                differentiator=body.brand.differentiator,
                slogan=body.brand.slogan,
            ))

    # Stores（先删旧的再插入，简单处理；后续 A9 可优化为 upsert）
    db.query(Store).filter(Store.enterprise_id == enterprise_id).delete()
    for st in body.stores:
        db.add(Store(
            enterprise_id=enterprise_id,
            name=st.name,
            city=st.city,
            district=st.district,
            address=st.address,
            phone=st.phone,
            business_hours=st.business_hours,
            is_primary=st.is_primary,
        ))

    # Services
    db.query(Service).filter(Service.enterprise_id == enterprise_id).delete()
    for sv in body.services:
        db.add(Service(
            enterprise_id=enterprise_id,
            name=sv.name,
            description=sv.description,
            category=sv.category,
            price_hint=sv.price_hint,
            duration_minutes=sv.duration_minutes,
            status="active",
        ))

    db.commit()
    logger.info(
        "[onboarding] side effects written eid=%s brands=%s stores=%s services=%s",
        enterprise_id,
        1 if body.brand else 0,
        len(body.stores),
        len(body.services),
    )

    # TargetEngine（不删，追加不重复的）
    existing_engines = {
        e.code for e in db.query(TargetEngine.code).filter(TargetEngine.enabled == True).all()  # noqa: E712
    }
    for code in body.target_engines:
        if code not in existing_engines:
            # TargetEngine 不是租户表，全局共享。只记录，不创建新引擎。
            # 用户的目标引擎选择存在 enterprises.settings 中。
            pass

    # 保存 target_engines 到 enterprise settings
    from app.models import Enterprise
    ent = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if ent:
        settings_json = ent.settings or {}
        settings_json["target_engines"] = body.target_engines
        ent.settings = settings_json
        db.commit()


def _bootstrap_kb(db, enterprise_id: int, body: OnboardingRunRequest, graph_state: dict):
    """入驻后自动建库：种子 Fact + 初始 Signal + thin_kb_check + llms.txt。"""
    from app.service.kb_service import FactService, SignalService
    from app.schemas.kb import KBFactCreate, KBSignalCreate
    from app.service.kb_freshness_service import thin_kb_check
    from app.models import Enterprise

    # 1. 写入种子 Fact
    fact_count = 0
    for sf in (body.seed_facts or []):
        try:
            FactService.create(db, enterprise_id, KBFactCreate(
                title=sf.title,
                content=sf.content,
                source_type="onboarding",
                tags=["入驻种子"],
                verified=False,
            ))
            fact_count += 1
        except Exception:
            pass

    # 2. 提取初始 Signal
    signal_count = 0
    signals_to_create = []

    # 从 raw_inputs 提取信号
    if body.raw_inputs.strip():
        signals_to_create.append(KBSignalCreate(
            signal_type="raw_input",
            content=body.raw_inputs[:2000],
            source="onboarding",
            status="pending",
        ))

    # 从 pain_points 提取信号
    pain_points = graph_state.get("pain_points") or graph_state.get("output_data", {}).get("pain_points", [])
    for pp in (pain_points or [])[:3]:
        point_text = pp.get("point", "") if isinstance(pp, dict) else str(pp)
        if point_text:
            severity = pp.get("severity", 5) if isinstance(pp, dict) else 5
            signals_to_create.append(KBSignalCreate(
                signal_type="pain_point",
                content=point_text[:1000],
                source="diagnosis",
                confidence=min(severity * 10, 100),
                status="pending",
            ))

    for sig in signals_to_create[:10]:  # 最多 10 条信号
        try:
            SignalService.create(db, enterprise_id, sig)
            signal_count += 1
        except Exception:
            pass

    # 3. thin_kb_check 验证
    thin_result = thin_kb_check(db, enterprise_id)

    # 4. 生成 llms.txt 骨架
    services = body.services or []
    store = body.stores[0] if body.stores else None
    brand_name = (body.brand.name if body.brand else None) or body.enterprise.name

    lines = [
        f"# {brand_name}",
        f"",
        f"## 品牌",
        f"- 名称：{brand_name}",
    ]
    if body.brand and body.brand.differentiator:
        lines.append(f"- 差异化：{body.brand.differentiator}")
    if body.brand and body.brand.slogan:
        lines.append(f"- Slogan：{body.brand.slogan}")

    lines.append("")
    lines.append("## 门店")
    if store:
        lines.append(f"- 名称：{store.name}")
        if store.address:
            lines.append(f"- 地址：{store.address}")
        if store.city or store.district:
            lines.append(f"- 区域：{store.city or ''}{store.district or ''}")
        if store.business_hours:
            lines.append(f"- 营业时间：{store.business_hours}")

    lines.append("")
    lines.append("## 服务项目")
    for sv in services:
        line = f"- {sv.name}"
        if sv.description:
            line += f"：{sv.description[:100]}"
        lines.append(line)

    lines.append("")
    lines.append("## 资质")
    lines.append(f"- 行业：{body.enterprise.industry}")
    if body.enterprise.license_no:
        lines.append(f"- 许可证：{body.enterprise.license_no}")

    llms_txt = "\n".join(lines)

    # 写入 enterprises.settings
    ent = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if ent:
        settings_json = dict(ent.settings or {})
        settings_json["llms_txt"] = llms_txt
        settings_json["hosted_page_url"] = f"/hosted/{enterprise_id}"  # 占位 URL，B5 替换
        settings_json["onboarding"] = {
            "completed_at": __import__("datetime").datetime.utcnow().isoformat(),
            "thin_kb": thin_result,
            "fact_count": fact_count,
            "signal_count": signal_count,
        }
        ent.settings = settings_json
        db.commit()

    logger.info(
        "[onboarding] kb bootstrap done eid=%s facts=%s signals=%s thin_kb=%s",
        enterprise_id, fact_count, signal_count, thin_result.get("passed"),
    )


@router.get("/status/{task_id}", response_model=AgentTaskResponse)
def onboarding_status(task_id: int, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    t = AgentTaskService.get(db, user.enterprise_id, task_id)
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "任务不存在")
    return t


@router.get("/events/{task_id}", summary="SSE 进度推送")
async def onboarding_events(
    task_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """SSE 端点 — 实时推送入驻进度。

    前端用 EventSource 连接，无需轮询。
    """
    from app.core.sse import subscribe_progress

    # 确认任务存在且属于当前用户
    t = AgentTaskService.get(db, user.enterprise_id, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="任务不存在")

    return StreamingResponse(
        subscribe_progress(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/snapshot", response_model=DashboardData, summary="返回当前企业 S3 三舱全量 Dashboard")
def onboarding_snapshot(user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    sp = StrategyPackService.ensure_draft_default(db, user.enterprise_id, user.id)
    items, total = ScenarioService.list(
        db,
        user.enterprise_id,
        type("P", (), {"channel": None, "skill": None, "status": None, "keyword": "", "page": 1, "page_size": 100})(),
    )
    return {
        "period": "onboarding",
        "kpi": {
            "total_scenarios": total,
            "total_drafts_published": 0,
            "avg_mention_rate": 0.0,
            "avg_trust_score": 0.0,
            "core_queries": 0,
            "probe_discoveries": 0,
            "pending_review": 0,
            "kb_facts_verified": 0,
        },
        "by_channel": [],
        "by_engine": [],
        "trend": [],
        "alerts": [],
        "scenarios": total,
        "strategy_pack_id": sp.id,
    }
