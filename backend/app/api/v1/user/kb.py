from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.api.deps import get_current_user
from app.api.common import require_role
from app.schemas import ResponseModel, ListResponse, MessageResponse, BulkIds
from app.schemas.kb import (
    KBFactCreate,
    KBFactUpdate,
    KBFactResponse,
    KBFactListParams,
    KBFaqCreate,
    KBFaqUpdate,
    KBFaqResponse,
    KBFaqListParams,
    KBSignalCreate,
    KBSignalUpdate,
    KBSignalResponse,
    KBSignalListParams,
    KBExternalCreate,
    KBExternalUpdate,
    KBExternalResponse,
    KBExternalListParams,
    KBSummary,
)
from app.service import (
    FactService,
    FaqService,
    SignalService,
    ExternalService,
    KBSummaryService,
)

router = APIRouter(
    prefix=f"{settings.API_V1_PREFIX}/user/kb",
    tags=["用户端·舱1·知识库"],
    dependencies=[Depends(get_current_user)],
)


def _eid(user) -> int:
    return user.enterprise_id


_WRITE_ROLES = ["editor", "admin", "owner"]


@router.get("/summary", response_model=ResponseModel[KBSummary])
def get_summary(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return ResponseModel(data=KBSummaryService.summary(db, _eid(current_user)))


@router.get("/freshness", response_model=ResponseModel[dict])
def get_kb_freshness(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    from app.service.kb_freshness_service import kb_freshness, thin_kb_check

    eid = _eid(current_user)
    return ResponseModel(data={
        "freshness": kb_freshness(db, eid),
        "thin_kb": thin_kb_check(db, eid),
    })


# ============== Facts ==============
@router.get("/facts", response_model=ListResponse[KBFactResponse])
def list_facts(
    params: KBFactListParams = Depends(),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = FactService.list(db, _eid(current_user), params)
    return ListResponse(
        total=total,
        page=params.page,
        page_size=params.page_size,
        items=[KBFactResponse.model_validate(FactService._post_load(i)) for i in items],
    )


@router.post("/facts", response_model=ResponseModel[KBFactResponse], status_code=201)
@require_role(_WRITE_ROLES)
def create_fact(
    data: KBFactCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    item = FactService.create(db, _eid(current_user), data)
    return ResponseModel(data=KBFactResponse.model_validate(item), message="已创建")


@router.get("/facts/{fact_id}", response_model=ResponseModel[KBFactResponse])
def get_fact(fact_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    item = FactService.get(db, _eid(current_user), fact_id)
    if not item:
        raise HTTPException(404, "Fact 不存在")
    return ResponseModel(data=KBFactResponse.model_validate(item))


@router.put("/facts/{fact_id}", response_model=ResponseModel[KBFactResponse])
@require_role(_WRITE_ROLES)
def update_fact(fact_id: int, data: KBFactUpdate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        item = FactService.update(db, _eid(current_user), fact_id, data)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return ResponseModel(data=KBFactResponse.model_validate(item), message="已更新")


@router.delete("/facts/{fact_id}", response_model=ResponseModel[MessageResponse])
@require_role(_WRITE_ROLES)
def delete_fact(fact_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        FactService.delete(db, _eid(current_user), fact_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return ResponseModel(data=MessageResponse(message="已删除"))


@router.post("/facts/bulk-delete", response_model=ResponseModel[MessageResponse])
@require_role(_WRITE_ROLES)
def bulk_delete_facts(data: BulkIds, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    eid = _eid(current_user)
    for fid in data.ids:
        try:
            FactService.delete(db, eid, fid)
        except ValueError:
            continue
    return ResponseModel(data=MessageResponse(message=f"已删除 {len(data.ids)} 条"))


# ============== FAQs ==============
@router.get("/faqs", response_model=ListResponse[KBFaqResponse])
def list_faqs(params: KBFaqListParams = Depends(), current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    items, total = FaqService.list(db, _eid(current_user), params)
    return ListResponse(
        total=total, page=params.page, page_size=params.page_size,
        items=[KBFaqResponse.model_validate(FaqService._post_load(i)) for i in items],
    )


@router.post("/faqs", response_model=ResponseModel[KBFaqResponse], status_code=201)
@require_role(_WRITE_ROLES)
def create_faq(data: KBFaqCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    item = FaqService.create(db, _eid(current_user), data)
    return ResponseModel(data=KBFaqResponse.model_validate(item), message="已创建")


@router.get("/faqs/{faq_id}", response_model=ResponseModel[KBFaqResponse])
def get_faq(faq_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    item = FaqService.get(db, _eid(current_user), faq_id)
    if not item:
        raise HTTPException(404, "FAQ 不存在")
    return ResponseModel(data=KBFaqResponse.model_validate(item))


@router.put("/faqs/{faq_id}", response_model=ResponseModel[KBFaqResponse])
@require_role(_WRITE_ROLES)
def update_faq(faq_id: int, data: KBFaqUpdate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        item = FaqService.update(db, _eid(current_user), faq_id, data)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return ResponseModel(data=KBFaqResponse.model_validate(item), message="已更新")


@router.delete("/faqs/{faq_id}", response_model=ResponseModel[MessageResponse])
@require_role(_WRITE_ROLES)
def delete_faq(faq_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        FaqService.delete(db, _eid(current_user), faq_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return ResponseModel(data=MessageResponse(message="已删除"))


# ============== Signals ==============
@router.get("/signals", response_model=ListResponse[KBSignalResponse])
def list_signals(params: KBSignalListParams = Depends(), current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    items, total = SignalService.list(db, _eid(current_user), params)
    return ListResponse(
        total=total, page=params.page, page_size=params.page_size,
        items=[KBSignalResponse.model_validate(SignalService._post_load(i)) for i in items],
    )


@router.post("/signals", response_model=ResponseModel[KBSignalResponse], status_code=201)
@require_role(_WRITE_ROLES)
def create_signal(data: KBSignalCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    it = SignalService.create(db, _eid(current_user), data)
    return ResponseModel(data=KBSignalResponse.model_validate(it), message="已创建")


@router.put("/signals/{signal_id}", response_model=ResponseModel[KBSignalResponse])
@require_role(_WRITE_ROLES)
def update_signal(signal_id: int, data: KBSignalUpdate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        it = SignalService.update(db, _eid(current_user), signal_id, data)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return ResponseModel(data=KBSignalResponse.model_validate(it), message="已更新")


@router.delete("/signals/{signal_id}", response_model=ResponseModel[MessageResponse])
@require_role(_WRITE_ROLES)
def delete_signal(signal_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        SignalService.delete(db, _eid(current_user), signal_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return ResponseModel(data=MessageResponse(message="已删除"))


# ============== Externals ==============
@router.get("/externals", response_model=ListResponse[KBExternalResponse])
def list_externals(params: KBExternalListParams = Depends(), current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    items, total = ExternalService.list(db, _eid(current_user), params)
    return ListResponse(
        total=total, page=params.page, page_size=params.page_size,
        items=[KBExternalResponse.model_validate(ExternalService._post_load(i)) for i in items],
    )


@router.post("/externals", response_model=ResponseModel[KBExternalResponse], status_code=201)
@require_role(_WRITE_ROLES)
def create_external(data: KBExternalCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    it = ExternalService.create(db, _eid(current_user), data)
    return ResponseModel(data=KBExternalResponse.model_validate(it), message="已创建")


@router.put("/externals/{ext_id}", response_model=ResponseModel[KBExternalResponse])
@require_role(_WRITE_ROLES)
def update_external(ext_id: int, data: KBExternalUpdate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        it = ExternalService.update(db, _eid(current_user), ext_id, data)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return ResponseModel(data=KBExternalResponse.model_validate(it), message="已更新")


@router.delete("/externals/{ext_id}", response_model=ResponseModel[MessageResponse])
@require_role(_WRITE_ROLES)
def delete_external(ext_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        ExternalService.delete(db, _eid(current_user), ext_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return ResponseModel(data=MessageResponse(message="已删除"))
