"""注册所有 bootstrap 钩子。"""
from __future__ import annotations

from app.infrastructure.bootstrap.init_manager import auto_init
from app.infrastructure.bootstrap.registrations.database import init_database
from app.infrastructure.bootstrap.registrations.embeddings import init_embeddings
from app.infrastructure.bootstrap.registrations.langgraph import init_langgraph, stop_langgraph
from app.infrastructure.bootstrap.registrations.langsmith import init_langsmith
from app.infrastructure.bootstrap.registrations.reranker import init_reranker
from app.infrastructure.bootstrap.registrations.sentry import init_sentry


def register_all() -> None:
    auto_init.register_init(
        init_sentry, name="sentry", priority=5, roles=("api", "worker"), critical=False
    )
    auto_init.register_init(
        init_langsmith, name="langsmith", priority=6, roles=("api", "worker"), critical=False
    )
    # create_all 失败在钩子内降级，不 raise；critical=False 避免本地无库时阻断启动
    auto_init.register_init(
        init_database, name="database", priority=10, critical=False
    )
    auto_init.register_init(
        init_langgraph,
        name="langgraph",
        priority=40,
        roles=("worker",),
        critical=False,
    )
    auto_init.register_init(
        init_embeddings,
        name="embeddings",
        priority=50,
        roles=("api", "worker"),
        critical=False,
    )
    auto_init.register_init(
        init_reranker,
        name="reranker",
        priority=55,
        roles=("worker",),
        critical=False,
    )
    auto_init.register_stop(
        stop_langgraph, name="langgraph_stop", priority=40, roles=("api", "worker")
    )


register_all()
