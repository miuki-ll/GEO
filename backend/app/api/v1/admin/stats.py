from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_platform_admin
from app.core.config import settings
from app.core.db import get_db
from app.models import User, Enterprise, AgentTask, ContentDraft, PublishTask
from app.schemas import ResponseModel

router = APIRouter(
    prefix=f"{settings.API_V1_PREFIX}/admin/stats",
    tags=["管理端·统计"],
    dependencies=[Depends(require_platform_admin)],
)


@router.get("/overview", response_model=ResponseModel[dict])
def platform_overview(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_platform_admin),
):
    return ResponseModel(
        data={
            "enterprises": db.query(Enterprise).count(),
            "users": db.query(User).count(),
            "agent_tasks": db.query(AgentTask).count(),
            "content_drafts": db.query(ContentDraft).count(),
            "publish_tasks": db.query(PublishTask).count(),
        }
    )
