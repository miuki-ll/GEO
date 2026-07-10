"""向后兼容层：鉴权依赖已合并至 app.core.security，此处仅 re-export 供路由引用。"""

from app.core.security import (
    oauth2_scheme,
    get_current_user,
    get_current_user_or_none,
    require_role,
    require_enterprise_owner_or_admin,
    require_platform_admin,
)

__all__ = [
    "oauth2_scheme",
    "get_current_user",
    "get_current_user_or_none",
    "require_role",
    "require_enterprise_owner_or_admin",
    "require_platform_admin",
]
