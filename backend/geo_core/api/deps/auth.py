from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from geo_core.core.config import settings
from geo_core.core.db import get_db
from geo_core.core.security import decode_token
from geo_core.models import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False
)


def get_current_user_or_none(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not token:
        return None
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        return None
    return user


def get_current_user(
    current_user: Optional[User] = Depends(get_current_user_or_none),
) -> User:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证或认证已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


def require_role(*roles: str):
    def _check(user: User = Depends(get_current_user)) -> User:
        if roles and user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足",
            )
        return user
    return _check


def require_enterprise_owner_or_admin(
    user: User = Depends(get_current_user),
) -> User:
    if user.role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅企业拥有者或管理员可执行此操作",
        )
    return user
