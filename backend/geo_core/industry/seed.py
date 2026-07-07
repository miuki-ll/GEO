from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from geo_core.industry.beauty_local import (
    BEAUTY_LOCAL_FACT_TEMPLATES,
    BEAUTY_LOCAL_SCENARIO_TEMPLATES,
    BEAUTY_LOCAL_DEFAULT_PERSONA,
    BEAUTY_LOCAL_COMPETITORS_TEMPLATE,
    BEAUTY_LOCAL_CHANNEL_WEIGHTS,
)
from geo_core.schemas.auth import UserCreate
from geo_core.schemas.business import (
    ScenarioCreate,
    StrategyPackCreate,
)
from geo_core.schemas.kb import KBFactCreate, KBSignalCreate
from geo_core.services import (
    UserService,
    FactService,
    SignalService,
    ScenarioService,
    StrategyPackService,
)
from geo_core.core.logging_config import get_logger

logger = get_logger(__name__)


def seed_beauty_enterprise(
    db: Session,
    enterprise_name: str = "倾城美业 · XX 路皮肤管理中心",
    user_email: str = "owner@example.com",
    user_password: str = "Admin@12345",
) -> Dict[str, Any]:
    """创建 AC 验收的种子企业 + 所有者 + 20 Fact + 5 Signal + 5 Scenario + 1 StrategyPack

    返回：{enterprise, owner, token_payload, facts, scenarios, strategy_pack}
    """
    user_reg = UserCreate(
        email=user_email,
        password=user_password,
        full_name="李美丽",
        phone="13800138000",
        role="owner",
        enterprise_name=enterprise_name,
        industry="beauty_local",
        city="上海市",
        district="静安区",
        address="XX 路 88 号商圈 2F",
        scale="5-10人",
        license_no="沪卫公卫字(2024)第 012345 号",
    )
    enterprise, owner = UserService.register(db, user_reg)
    token = UserService.issue_token(owner)

    facts = []
    for group in BEAUTY_LOCAL_FACT_TEMPLATES:
        for i, claim in enumerate(group["facts"]):
            f = FactService.create(
                db,
                enterprise.id,
                KBFactCreate(
                    title=f"{group['title']} - {i + 1}",
                    content=claim,
                    source_type="official",
                    source_ref="https://store.example.com/about/#qualification",
                    category=group["category"],
                    tags=group["tags"],
                    verified=True,
                ),
            )
            facts.append(f)

    signals = []
    for kw in ["敏感肌 推荐", "补水 美容院 项目", "换季 泛红 怎么办", "皮肤管理中心 推荐", "痘痘肌 护理"]:
        signals.append(
            SignalService.create(
                db,
                enterprise.id,
                KBSignalCreate(
                    signal_type="keyword",
                    content=kw,
                    source="manual_seed",
                    confidence=85,
                    status="active",
                    metadata={"engines": ["豆包", "DeepSeek"]},
                ),
            )
        )

    scenarios = []
    for sc in BEAUTY_LOCAL_SCENARIO_TEMPLATES:
        fact_refs = [f.id for f in facts[:5]]
        sc_obj = ScenarioService.create(
            db,
            enterprise.id,
            ScenarioCreate(
                **sc,
                fact_refs=fact_refs,
                persona_ref=BEAUTY_LOCAL_DEFAULT_PERSONA,
                competitor_ref={
                    "benchmark": [c["name"] for c in BEAUTY_LOCAL_COMPETITORS_TEMPLATE[:2]]
                },
            ),
        )
        scenarios.append(sc_obj)

    strategy = StrategyPackService.create(
        db,
        enterprise.id,
        StrategyPackCreate(
            version="beauty-seed-v1.0",
            persona=BEAUTY_LOCAL_DEFAULT_PERSONA,
            competitors=BEAUTY_LOCAL_COMPETITORS_TEMPLATE,
            pain_points=[
                {
                    "point": "资质与卫生宣传缺失",
                    "severity": 8,
                    "evidence": "AI 回答极少提及资质",
                    "scenario_ids": [s.id for s in scenarios[:1]],
                },
                {
                    "point": "成分信息不明",
                    "severity": 7,
                    "evidence": "敏感肌对话中产品成分命中率低",
                },
            ],
            scenarios=[
                {
                    "id": s.id,
                    "title": s.title,
                    "channel": s.channel,
                    "skill": s.skill,
                    "priority": s.priority,
                    "target_engines": s.target_engines if hasattr(s, "target_engines") else [],
                }
                for s in scenarios
            ],
            channels=BEAUTY_LOCAL_CHANNEL_WEIGHTS,
            weights={"persona": 0.3, "competitors": 0.3, "channels": 0.2, "scenarios": 0.2},
            metadata={"seed": "beauty_local", "created_at": datetime.utcnow().isoformat()},
        ),
        owner.id,
    )

    logger.info(
        "seed_beauty_enterprise done: eid=%s owner=%s facts=%d scenarios=%d",
        enterprise.id, owner.id, len(facts), len(scenarios),
    )
    return {
        "enterprise": enterprise,
        "owner": owner,
        "token": token,
        "facts": facts,
        "signals": signals,
        "scenarios": scenarios,
        "strategy_pack": strategy,
        "seeded": True,
        "fact_count": len(facts),
        "signal_count": len(signals),
        "scenario_count": len(scenarios),
    }
