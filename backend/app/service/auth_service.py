from typing import Optional, Tuple, List
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings
from app.core.logging_config import get_logger
from app.models import Enterprise, User
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponse,
    TokenPayload,
    EnterpriseCreate,
    EnterpriseUpdate,
    EnterpriseResponse,
    MemberInvite,
    MemberListParams,
    role_can_manage,
)

logger = get_logger(__name__)


class EnterpriseService:
    @staticmethod
    def create(db: Session, data: EnterpriseCreate) -> Enterprise:
        # 检查企业名唯一
        existing = db.query(Enterprise).filter(Enterprise.name == data.name).first()
        if existing:
            raise ValueError("该企业名称已被注册")
        ent = Enterprise(**data.model_dump())
        ent.status = "active"
        db.add(ent)
        db.commit()
        db.refresh(ent)
        logger.info("Created enterprise id=%s name=%s", ent.id, ent.name)
        return ent

    @staticmethod
    def get(db: Session, enterprise_id: int) -> Optional[Enterprise]:
        return db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()

    @staticmethod
    def update(db: Session, enterprise_id: int, data: EnterpriseUpdate) -> Enterprise:
        ent = EnterpriseService.get(db, enterprise_id)
        if not ent:
            raise ValueError("企业不存在")
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(ent, k, v)
        db.commit()
        db.refresh(ent)
        return ent

    @staticmethod
    def touch_kb(db: Session, enterprise_id: int) -> None:
        ent = EnterpriseService.get(db, enterprise_id)
        if ent:
            ent.kb_updated_at = datetime.utcnow()
            db.commit()

    @staticmethod
    def to_response(ent: Enterprise) -> EnterpriseResponse:
        return EnterpriseResponse.model_validate(ent)


class UserService:
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email.lower().strip()).first()

    @staticmethod
    def list_members(
        db: Session, enterprise_id: int, params: MemberListParams
    ) -> Tuple[List[User], int]:
        q = db.query(User).filter(User.enterprise_id == enterprise_id)
        if params.role:
            q = q.filter(User.role == params.role)
        if params.status == "active":
            q = q.filter(User.is_active == True)  # noqa: E712
        elif params.status == "inactive":
            q = q.filter(User.is_active == False)  # noqa: E712
        if params.keyword:
            kw = f"%{params.keyword}%"
            q = q.filter((User.email.ilike(kw)) | (User.full_name.ilike(kw)))
        total = q.count()
        items = (
            q.order_by(User.created_at.desc())
            .offset((params.page - 1) * params.page_size)
            .limit(params.page_size)
            .all()
        )
        return items, total

    @staticmethod
    def register(db: Session, data: UserCreate) -> Tuple[Enterprise, User]:
        if UserService.get_by_email(db, data.email):
            raise ValueError("该邮箱已注册")
        ent_data = EnterpriseCreate(
            name=data.enterprise_name,
            industry=data.industry,
            license_no=data.license_no,
            contact_name=data.full_name,
            contact_phone=data.contact_phone,
            contact_email=data.email,
        )
        enterprise = EnterpriseService.create(db, ent_data)
        user = User(
            enterprise_id=enterprise.id,
            email=data.email.lower().strip(),
            full_name=data.full_name,
            phone=data.phone,
            avatar=data.avatar,
            hashed_password=get_password_hash(data.password),
            role="owner",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Registered owner user id=%s email=%s", user.id, user.email)
        return enterprise, user

    @staticmethod
    def authenticate(db: Session, data: UserLogin) -> Optional[User]:
        user = UserService.get_by_email(db, data.email)
        if not user or not user.is_active:
            return None
        if not verify_password(data.password, user.hashed_password):
            return None
        user.last_login_at = datetime.utcnow()
        db.commit()
        return user

    @staticmethod
    def issue_token(user: User) -> TokenPayload:
        expires_min = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        token = create_access_token(subject=user.id)
        return TokenPayload(
            access_token=token,
            token_type="bearer",
            expires_in=expires_min * 60,
            user=UserResponse.model_validate(user),
        )

    @staticmethod
    def invite_member(
        db: Session, enterprise_id: int, actor: User, data: MemberInvite
    ) -> User:
        if not role_can_manage(actor.role, data.role):
            raise ValueError("无权限邀请该角色的成员")
        if UserService.get_by_email(db, data.email):
            raise ValueError("该邮箱已加入企业，可直接登录")
        temp_pwd = "TMP_" + datetime.utcnow().strftime("%Y%m%d%H%M%S")
        user = User(
            enterprise_id=enterprise_id,
            email=data.email.lower().strip(),
            full_name=data.full_name,
            hashed_password=get_password_hash(temp_pwd),
            role=data.role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(
            "Invited member id=%s email=%s role=%s by %s",
            user.id,
            user.email,
            user.role,
            actor.id,
        )
        return user

    @staticmethod
    def update_user(
        db: Session,
        actor: User,
        target_id: int,
        data: UserUpdate,
    ) -> User:
        target = UserService.get_by_id(db, target_id)
        if not target or target.enterprise_id != actor.enterprise_id:
            raise ValueError("目标用户不存在")
        if target.id != actor.id:
            if not role_can_manage(actor.role, target.role):
                raise ValueError("无权限管理该成员")
        update_dict = data.model_dump(exclude_unset=True)
        if "role" in update_dict and target.id != actor.id:
            if not role_can_manage(actor.role, update_dict["role"]):
                raise ValueError("无权限设置该角色")
        for k, v in update_dict.items():
            setattr(target, k, v)
        db.commit()
        db.refresh(target)
        return target

    @staticmethod
    def to_response(user: User) -> UserResponse:
        return UserResponse.model_validate(user)
