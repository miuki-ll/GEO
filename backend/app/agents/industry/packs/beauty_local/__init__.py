"""Beauty local industry pack（懒导出，避免 import 即拉 seed/sqlalchemy）。"""

__all__ = ["get_beauty_industry_templates", "seed_beauty_enterprise"]


def __getattr__(name: str):
    if name == "get_beauty_industry_templates":
        from app.agents.industry.packs.beauty_local.templates import get_beauty_industry_templates

        return get_beauty_industry_templates
    if name == "seed_beauty_enterprise":
        from app.agents.industry.packs.beauty_local.seed import seed_beauty_enterprise

        return seed_beauty_enterprise
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
