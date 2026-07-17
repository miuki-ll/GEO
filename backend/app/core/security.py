"""密码哈希、JWT、OAuth2 依赖与权限校验（合并原 deps/auth 逻辑）。"""
from datetime import datetime, timedelta
from typing import Any, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Argon2 密码哈希上下文（Password Hash Context，密码加密工具）
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# OAuth2 Bearer 提取器：从 Authorization 头读取 Token，无 Token 时不自动报错
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False
)


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """生成 JWT Access Token（访问令牌），payload 含 sub（用户 ID）与 type=access。"""
    try:
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    except Exception as e:
        logger.exception("create_access_token 失败 subject=%s: %s", subject, e)
        raise RuntimeError("Token 生成失败") from e


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与数据库哈希是否匹配；异常时视为不匹配返回 False。"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.warning("verify_password 异常: %s", e)
        return False


def get_password_hash(password: str) -> str:
    """将明文密码转为 Argon2 哈希字符串，供注册/邀请成员时写入数据库。"""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.exception("get_password_hash 失败: %s", e)
        raise RuntimeError("密码加密失败") from e


def decode_token(token: str) -> dict | None:
    """解析并校验 JWT；签名无效或过期时返回 None。"""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except Exception as e:
        logger.debug("decode_token 失败: %s", e)
        return None


def _is_demo_token(token: str) -> bool:
    return bool(token) and token.startswith("demo-token-")


def _ensure_demo_user(db: Session) -> Optional["User"]:
    """开发环境：为前端占位 demo-token 准备/复用 demo@geo.test，并灌入演示数据。"""
    from app.models import Enterprise, User

    user = db.query(User).filter(User.email == "demo@geo.test").first()
    if not (user and user.is_active):
        ent = Enterprise(
            name="Demo 美业店",
            industry="beauty_local",
            industry_pack="beauty_local",
            status="active",
            plan="mvp",
            contact_email="demo@geo.test",
        )
        db.add(ent)
        db.flush()
        user = User(
            enterprise_id=ent.id,
            email="demo@geo.test",
            full_name="Demo User",
            hashed_password=get_password_hash("demo123456"),
            role="owner",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("dev demo user created id=%s enterprise_id=%s", user.id, ent.id)

    try:
        from app.dev_seed import ensure_tenant_seed_data

        ensure_tenant_seed_data(db, user.enterprise_id, user.id)
    except Exception as e:
        logger.warning("demo tenant seed skipped/failed: %s", e)
    return user


def get_current_user_or_none(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional["User"]:
    """FastAPI 依赖：尝试从 Bearer Token 解析当前用户；无效时返回 None（不抛错）。"""
    from app.models import User

    try:
        if not token:
            return None
        # MVP：前端 Login 仍发 demo-token-*；仅 development 放行
        if settings.is_dev and _is_demo_token(token):
            return _ensure_demo_user(db)
        payload = decode_token(token)
        if not payload:
            return None
        if payload.get("type") not in (None, "access"):
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            return None
        return user
    except Exception as e:
        logger.warning("get_current_user_or_none 异常: %s", e)
        return None


def get_current_user(
    current_user: Optional["User"] = Depends(get_current_user_or_none),
) -> "User":
    """FastAPI 依赖：要求已登录；未认证或 Token 无效时抛出 401。"""
    try:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未认证或认证已过期",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_current_user 异常: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def require_role(*roles: str):
    """工厂函数：生成「限定企业角色」的 FastAPI 依赖；角色不在列表内时 403。"""

    def _check(user: "User" = Depends(get_current_user)) -> "User":
        """校验当前用户 role 是否在允许列表中。"""
        try:
            if roles and user.role not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足",
                )
            return user
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("require_role 校验异常 roles=%s: %s", roles, e)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限校验失败",
            ) from e

    return _check


def require_enterprise_owner_or_admin(
    user: "User" = Depends(get_current_user),
) -> "User":
    """FastAPI 依赖：仅允许企业 owner 或 admin 访问（成员管理等敏感操作）。"""
    try:
        if user.role not in ("owner", "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="仅企业拥有者或管理员可执行此操作",
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("require_enterprise_owner_or_admin 异常 user_id=%s: %s", user.id, e)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限校验失败",
        ) from e


def require_platform_admin(
    user: "User" = Depends(get_current_user),
) -> "User":
    """FastAPI 依赖：平台管理端鉴权；role=platform_admin 或邮箱在白名单内可通过。"""
    try:
        allowed_emails = settings.platform_admin_email_set
        if user.role == "platform_admin" or user.email.lower() in allowed_emails:
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要平台管理员权限",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("require_platform_admin 异常 user_id=%s: %s", user.id, e)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="平台管理员权限校验失败",
        ) from e
