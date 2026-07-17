"""LangGraph agents + L3 industry packs（懒加载，避免 import 即拉 sqlalchemy）。"""

__all__ = ["run_graph", "register_graph", "list_graphs", "get_industry_pack", "list_industry_packs"]


def __getattr__(name: str):
    if name == "run_graph":
        from app.agents.runner import run_graph

        return run_graph
    if name in ("register_graph", "list_graphs"):
        from app.agents.registry import register_graph, list_graphs

        return register_graph if name == "register_graph" else list_graphs
    if name in ("get_industry_pack", "list_industry_packs"):
        from app.agents.industry import get_industry_pack, list_industry_packs

        return get_industry_pack if name == "get_industry_pack" else list_industry_packs
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
