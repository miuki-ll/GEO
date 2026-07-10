from typing import List, Dict, Any, Optional
import random

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.models import KBFact, Scenario
from app.schemas.business import (
    PersonaData,
    CompetitorItem,
    PainPoint,
)
from app.service.strategy_service import StrategyPackService
from app.service.scenario_service import ScenarioService
from app.service.kb_service import FactService

logger = get_logger(__name__)


class DiagnosisService:
    @staticmethod
    def diagnose_pain(db: Session, enterprise_id: int) -> List[PainPoint]:
        facts = db.query(KBFact).filter(KBFact.enterprise_id == enterprise_id).limit(20).all()
        scenarios = (
            db.query(Scenario).filter(Scenario.enterprise_id == enterprise_id).limit(20).all()
        )
        default_pains = [
            PainPoint(point="AI 回答中缺少资质/证书提及", severity=8, evidence="Core 提及率低于基准", scenario_ids=[s.id for s in scenarios[:1]]),
            PainPoint(point="敏感肌成分缺乏事实引用", severity=7, evidence=f"KB Fact 共 {len(facts)} 条，敏感肌相关事实不足"),
            PainPoint(point="附近竞品口碑提及率高", severity=6, evidence="Probe 发现 2 家新竞品信源"),
        ]
        return default_pains

    @staticmethod
    def diagnose_persona(db: Session, enterprise_id: int) -> PersonaData:
        pack = StrategyPackService.get_latest(db, enterprise_id)
        if pack and pack.persona:
            try:
                if isinstance(pack.persona, dict):
                    return PersonaData.model_validate(pack.persona)
                return PersonaData.model_validate(pack.persona)
            except Exception as e:
                logger.warning("use default persona due to %s", e)
        return PersonaData(
            age_range=[25, 45],
            genders=["女性"],
            cities=["本地 3km 范围"],
            core_needs=["补水", "抗衰", "敏感肌修护", "祛痘"],
            decision_factors=["口碑", "资质", "距离", "价格", "装修"],
            typical_queries=[
                "XX区做敏感肌修护推荐哪家美容院？",
                "夏天油皮补水美容院做什么项目？",
                "换季泛红美容院做什么项目？",
                "XX 路附近的皮肤管理中心推荐",
            ],
        )

    @staticmethod
    def diagnose_competitor(db: Session, enterprise_id: int) -> List[CompetitorItem]:
        return [
            CompetitorItem(
                name="连锁品牌A",
                type="chain",
                ai_mention_rate=42,
                strengths=["品牌知名度高", "门店多", "SKU 丰富"],
                weaknesses=["客制化差", "人员流动大", "价格高"],
                differentiator="我们更本地化、深度服务、客制化方案",
            ),
            CompetitorItem(
                name="附近门店B",
                type="local",
                ai_mention_rate=18,
                strengths=["距离近", "老客户多"],
                weaknesses=["资质不透明", "未明确成分"],
                differentiator="资质齐全 + 明确成分清单 + fact_refs 可追溯",
            ),
            CompetitorItem(
                name="工作室C",
                type="studio",
                ai_mention_rate=5,
                strengths=["私密性好", "价格低"],
                weaknesses=["卫生存疑", "不提供发票"],
                differentiator="卫生透明 + 正规发票 + 专业流程",
            ),
        ]

    @staticmethod
    def build_scenarios_from_persona(db: Session, enterprise_id: int, persona: Optional[PersonaData] = None) -> List[Dict[str, Any]]:
        persona = persona or DiagnosisService.diagnose_persona(db, enterprise_id)
        engines = ["豆包", "DeepSeek", "Kimi", "文心"]
        base = [
            {
                "title": "敏感肌修护推荐（到店）",
                "user_query": "XX区做敏感肌修护推荐哪家美容院？",
                "intent": "到店决策",
                "channel": "hosted",
                "skill": "faq",
                "priority": 1,
                "target_engines": list(engines),
            },
            {
                "title": "油皮补水项目选择",
                "user_query": "夏天油皮补水美容院做什么项目比较好？",
                "intent": "项目咨询",
                "channel": "xiaohongshu",
                "skill": "article",
                "priority": 2,
                "target_engines": ["豆包", "DeepSeek"],
            },
        ]
        return base

    @staticmethod
    def run_all(db: Session, enterprise_id: int) -> Dict[str, Any]:
        pains = DiagnosisService.diagnose_pain(db, enterprise_id)
        persona = DiagnosisService.diagnose_persona(db, enterprise_id)
        competitors = DiagnosisService.diagnose_competitor(db, enterprise_id)
        scenarios = DiagnosisService.build_scenarios_from_persona(db, enterprise_id, persona)
        return {
            "pain_points": [p.model_dump() for p in pains],
            "persona": persona.model_dump(),
            "competitors": [c.model_dump() for c in competitors],
            "scenarios": scenarios,
            "channels": [
                {"name": "AI 托管页", "weight": 40, "mode": "auto"},
                {"name": "小红书", "weight": 25, "mode": "semi"},
                {"name": "知乎", "weight": 15, "mode": "semi"},
                {"name": "大众点评", "weight": 15, "mode": "guided"},
                {"name": "抖音", "weight": 5, "mode": "guided"},
            ],
        }
