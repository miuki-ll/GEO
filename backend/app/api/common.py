from app.api.deps import (
    oauth2_scheme,
    get_current_user,
    get_current_user_or_none,
    require_enterprise_owner_or_admin,
)
from app.api.deps import require_role as _require_role_dep
from app.models import User
from fastapi import Depends, HTTPException, status
from typing import Sequence, Union, Callable, Any
from functools import wraps
import inspect

get_current_active_user = get_current_user


def require_role(roles: Union[str, Sequence[str]]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """真正的路由装饰器工厂：同时兼容 @require_role(["owner"]) 用法。

    内部仍然通过 FastAPI Depends(get_current_user) 注入 user，然后进行角色校验。
    支持同步和异步路由函数，且不会重复给已带 user 参数的函数注入冲突。
    """
    if isinstance(roles, str):
        rt = (roles,)
    elif isinstance(roles, (list, tuple, set)):
        rt = tuple(roles)
    else:
        rt = tuple(roles) if roles else ()

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        original_sig = inspect.signature(func)
        original_params = list(original_sig.parameters.values())

        def _check(user: User) -> None:
            if rt and user.role not in rt:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要角色：{','.join(rt)}",
                )

        user_param_needed = "user" not in original_sig.parameters

        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, user: User = Depends(get_current_active_user), **kwargs):
                _check(user)
                try:
                    bound = original_sig.bind_partial(*args, user=user, **kwargs)
                except TypeError:
                    bound = original_sig.bind_partial(*args, **kwargs)
                return await func(*bound.args, **bound.kwargs)
            wrapper = async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, user: User = Depends(get_current_active_user), **kwargs):
                _check(user)
                try:
                    bound = original_sig.bind_partial(*args, user=user, **kwargs)
                except TypeError:
                    bound = original_sig.bind_partial(*args, **kwargs)
                return func(*bound.args, **bound.kwargs)
            wrapper = sync_wrapper

        new_params = [p for p in original_params if p.name != "user"]
        user_param = inspect.Parameter(
            "user", inspect.Parameter.KEYWORD_ONLY,
            default=Depends(get_current_active_user), annotation=User,
        )
        inserted = False
        for i, p in enumerate(new_params):
            if p.kind == inspect.Parameter.VAR_KEYWORD:
                new_params.insert(i, user_param)
                inserted = True
                break
        if not inserted:
            new_params.append(user_param)
        wrapper.__signature__ = original_sig.replace(parameters=new_params)
        return wrapper

    return decorator


__all__ = [
    "oauth2_scheme",
    "get_current_user",
    "get_current_active_user",
    "get_current_user_or_none",
    "require_role",
    "require_enterprise_owner_or_admin",
]
