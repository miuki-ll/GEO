"""
GEO API v1 路由聚合 — 对齐 TalentFlow app/main.py 注册方式。

- v1 根目录：共用横切（auth / llm / agent）
- v1/user/：企业用户端 · 按业务域拆分
- v1/admin/：平台管理端 · 按业务域拆分

每个 router 文件自带完整 prefix（如 /api/v1/auth），此处不再叠加 prefix。
"""
from fastapi import APIRouter

from app.api.v1 import agent, auth, llm
from app.api.v1.admin import agent_traces, enterprises, llm as admin_llm, stats, users
from app.api.v1.user import (
    content,
    diagnosis,
    enterprise,
    kb,
    monitoring,
    onboarding,
    outcomes,
    publish,
    strategy_pack,
)

api_router = APIRouter()

# ── 共用（用户端 + 管理端 / 横切能力，类比 TalentFlow auth/jobs/skills/tasks）──
api_router.include_router(auth.router)
api_router.include_router(llm.router)
api_router.include_router(agent.router)

# ── 用户端 · 舱1 懂我 ──
api_router.include_router(enterprise.router)
api_router.include_router(kb.router)
api_router.include_router(onboarding.router)
api_router.include_router(diagnosis.router)

# ── 用户端 · 舱2 定方案 ──
api_router.include_router(strategy_pack.router)
api_router.include_router(content.router)

# ── 用户端 · 舱3 出结果 ──
api_router.include_router(publish.router)
api_router.include_router(monitoring.router)
api_router.include_router(outcomes.router)

# ── 管理端 · 平台运维 ──
api_router.include_router(enterprises.router)
api_router.include_router(users.router)
api_router.include_router(stats.router)
api_router.include_router(agent_traces.router)
api_router.include_router(admin_llm.router)
