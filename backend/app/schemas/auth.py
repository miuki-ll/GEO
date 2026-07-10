from typing import Optional, List
from pydantic import Field, EmailStr, field_validator
from datetime import datetime

from app.schemas import BaseSchema, IDModel, TimestampResponse, PaginationParams


class UserBase(BaseSchema):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = None
    avatar: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)
    enterprise_name: str = Field(..., min_length=1, max_length=200)
    industry: str = "beauty_local"
    license_no: Optional[str] = None
    contact_phone: Optional[str] = None


class UserLogin(BaseSchema):
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserUpdate(BaseSchema):
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = None
    avatar: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase, IDModel, TimestampResponse):
    enterprise_id: int
    role: str
    is_active: bool
    last_login_at: Optional[datetime] = None


class TokenPayload(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class EnterpriseBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=200)
    industry: str = "beauty_local"
    license_no: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    plan: str = "mvp"


class EnterpriseCreate(EnterpriseBase):
    pass


class EnterpriseUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    industry: Optional[str] = None
    license_no: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    settings: Optional[dict] = None


class EnterpriseResponse(EnterpriseBase, IDModel, TimestampResponse):
    status: str
    settings: Optional[dict] = {}
    kb_updated_at: Optional[datetime] = None


class MemberInvite(BaseSchema):
    email: EmailStr
    full_name: str
    role: str = "member"
    send_email: bool = True

    @field_validator("role")
    @classmethod
    def valid_role(cls, v: str) -> str:
        allowed = {"owner", "admin", "editor", "member", "viewer"}
        if v not in allowed:
            raise ValueError(f"role 必须是 {sorted(allowed)} 之一")
        return v


class MemberListParams(PaginationParams):
    role: Optional[str] = None
    status: Optional[str] = None


ROLE_HIERARCHY = {
    "owner": 100,
    "admin": 80,
    "editor": 50,
    "member": 30,
    "viewer": 10,
}


def role_can_manage(actor_role: str, target_role: str) -> bool:
    return ROLE_HIERARCHY.get(actor_role, 0) > ROLE_HIERARCHY.get(target_role, 0)
