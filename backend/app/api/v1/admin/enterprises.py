from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_platform_admin
from app.core.config import settings
from app.core.db import get_db
from app.models import Enterprise, User
from app.schemas import ResponseModel, ListResponse
from app.schemas.auth import EnterpriseResponse

router = APIRouter(
    prefix=f"{settings.API_V1_PREFIX}/admin/enterprises",
    tags=["管理端·企业"],
    dependencies=[Depends(require_platform_admin)],
)


@router.get("", response_model=ListResponse[EnterpriseResponse])
def list_enterprises(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_platform_admin),
):
    q = db.query(Enterprise)
    if status:
        q = q.filter(Enterprise.status == status)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(Enterprise.name.ilike(kw))
    total = q.count()
    items = (
        q.order_by(Enterprise.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[EnterpriseResponse.model_validate(i) for i in items],
    )


@router.get("/{enterprise_id}", response_model=ResponseModel[EnterpriseResponse])
def get_enterprise(
    enterprise_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_platform_admin),
):
    ent = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if not ent:
        from fastapi import HTTPException

        raise HTTPException(404, "企业不存在")
    return ResponseModel(data=EnterpriseResponse.model_validate(ent))
