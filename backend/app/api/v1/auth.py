"""共用 · 认证授权 — 用户端 / 管理端均走此路由（对齐 TalentFlow app/api/v1/auth.py）。"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.logging_config import get_logger
from app.api.deps import get_current_user
from app.schemas import ResponseModel
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    TokenPayload,
    UserResponse,
)
from app.service import UserService

router = APIRouter(prefix=f"{settings.API_V1_PREFIX}/auth", tags=["认证授权"])
logger = get_logger(__name__)


@router.post("/register", response_model=ResponseModel[TokenPayload])
def register(data: UserCreate, db: Session = Depends(get_db)):
    """注册新企业与 owner 账号，成功后签发 JWT 并返回 TokenPayload。"""
    try:
        _, user = UserService.register(db, data)
        token = UserService.issue_token(user)
        return ResponseModel(data=token, message="注册成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("register 失败 email=%s: %s", data.email, e)
        raise HTTPException(status_code=500, detail="注册失败，请稍后重试") from e


@router.post("/login", response_model=ResponseModel[TokenPayload])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """OAuth2 表单登录（Swagger 兼容）；username 字段填邮箱。"""
    try:
        data = UserLogin(email=form_data.username, password=form_data.password)
        user = UserService.authenticate(db, data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = UserService.issue_token(user)
        return ResponseModel(data=token)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("login 失败 username=%s: %s", form_data.username, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试",
        ) from e


@router.post("/login/json-login", response_model=ResponseModel[TokenPayload])
def json_login(data: UserLogin, db: Session = Depends(get_db)):
    """JSON 体登录（前端常用）；body 为 { email, password }。"""
    try:
        user = UserService.authenticate(db, data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误",
            )
        token = UserService.issue_token(user)
        return ResponseModel(data=token)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("json_login 失败 email=%s: %s", data.email, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试",
        ) from e


@router.get("/me", response_model=ResponseModel[UserResponse])
def get_me(current_user=Depends(get_current_user)):
    """获取当前登录用户信息（需 Bearer Token）。"""
    try:
        return ResponseModel(data=UserService.to_response(current_user))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_me 失败 user_id=%s: %s", getattr(current_user, "id", None), e)
        raise HTTPException(status_code=500, detail="获取用户信息失败") from e


@router.post("/refresh", response_model=ResponseModel[TokenPayload])
def refresh(current_user=Depends(get_current_user)):
    """在 Token 仍有效时重新签发新 JWT（延长会话）。"""
    try:
        token = UserService.issue_token(current_user)
        return ResponseModel(data=token, message="已刷新 token")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("refresh 失败 user_id=%s: %s", getattr(current_user, "id", None), e)
        raise HTTPException(status_code=500, detail="Token 刷新失败") from e
