from fastapi import APIRouter, Depends

from app.api.deps import require_platform_admin
from app.core.config import settings
from app.core.llm import get_total_usage, list_available_engines
from app.models import User
from app.schemas import ResponseModel

router = APIRouter(
    prefix=f"{settings.API_V1_PREFIX}/admin/llm",
    tags=["管理端·LLM"],
    dependencies=[Depends(require_platform_admin)],
)


@router.get("/usage", response_model=ResponseModel[dict])
def platform_llm_usage(_admin: User = Depends(require_platform_admin)):
    usage = get_total_usage()
    return ResponseModel(
        data={
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "engines": list_available_engines(),
        }
    )
