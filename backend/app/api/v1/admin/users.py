from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_platform_admin
from app.core.config import settings
from app.core.db import get_db
from app.models import User
from app.schemas import ListResponse
from app.schemas.auth import UserResponse

router = APIRouter(
    prefix=f"{settings.API_V1_PREFIX}/admin/users",
    tags=["管理端·用户"],
    dependencies=[Depends(require_platform_admin)],
)


@router.get("", response_model=ListResponse[UserResponse])
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    enterprise_id: int | None = None,
    role: str | None = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_platform_admin),
):
    q = db.query(User)
    if enterprise_id:
        q = q.filter(User.enterprise_id == enterprise_id)
    if role:
        q = q.filter(User.role == role)
    total = q.count()
    items = (
        q.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[UserResponse.model_validate(u) for u in items],
    )
