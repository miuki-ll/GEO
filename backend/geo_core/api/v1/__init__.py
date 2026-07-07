from fastapi import APIRouter

from geo_core.api.v1 import auth, enterprise, kb, llm, onboarding, diagnosis, strategy_pack
from geo_core.api.v1 import content, publish, monitoring, outcomes, agent

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(enterprise.router, prefix="/enterprise", tags=["企业/成员"])
api_router.include_router(kb.router, prefix="/kb", tags=["知识库"])
api_router.include_router(llm.router, prefix="/llm", tags=["LLM Gateway"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["开店向导"])
api_router.include_router(diagnosis.router, prefix="/diagnosis", tags=["诊断分析"])
api_router.include_router(strategy_pack.router, prefix="/strategy-pack", tags=["方案包"])
api_router.include_router(content.router, prefix="/content", tags=["内容生产"])
api_router.include_router(publish.router, prefix="/publish", tags=["发布引擎"])
api_router.include_router(monitoring.router, prefix="/monitor", tags=["监测体系"])
api_router.include_router(outcomes.router, prefix="/outcomes", tags=["效果舱"])
api_router.include_router(agent.router, prefix="/agent", tags=["Agent任务"])
