from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from geo_core.core.db import get_db
from geo_core.core.config import settings
from geo_core.api.deps import get_current_user
from geo_core.schemas import ResponseModel
from geo_core.schemas.auth import (
    UserCreate,
    UserLogin,
    TokenPayload,
    UserResponse,
)
from geo_core.services import UserService, EnterpriseService

router = APIRouter()


@router.post("/register", response_model=ResponseModel[TokenPayload])
def register(data: UserCreate, db: Session = Depends(get_db)):
    try:
        enterprise, user = UserService.register(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    token = UserService.issue_token(user)
    return ResponseModel(data=token, message="注册成功")


@router.post("/login", response_model=ResponseModel[TokenPayload])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
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


@router.post("/login/json-login", response_model=ResponseModel[TokenPayload])
def json_login(data: UserLogin, db: Session = Depends(get_db)):
    user = UserService.authenticate(db, data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )
    token = UserService.issue_token(user)
    return ResponseModel(data=token)


@router.get("/me", response_model=ResponseModel[UserResponse])
def get_me(current_user=Depends(get_current_user)):
    return ResponseModel(data=UserService.to_response(current_user))


@router.post("/refresh", response_model=ResponseModel[TokenPayload])
def refresh(current_user=Depends(get_current_user)):
    token = UserService.issue_token(current_user)
    return ResponseModel(data=token, message="已刷新 token")
