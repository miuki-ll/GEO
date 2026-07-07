from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from geo_core.core.db import get_db
from geo_core.api.deps import (
    get_current_user,
    require_enterprise_owner_or_admin,
)
from geo_core.schemas import ResponseModel, ListResponse
from geo_core.schemas.auth import (
    EnterpriseUpdate,
    EnterpriseResponse,
    MemberInvite,
    MemberListParams,
    UserResponse,
    UserUpdate,
)
from geo_core.services import EnterpriseService, UserService

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/profile", response_model=ResponseModel[EnterpriseResponse])
def get_profile(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    ent = EnterpriseService.get(db, current_user.enterprise_id)
    if not ent:
        raise HTTPException(404, "企业不存在")
    return ResponseModel(data=EnterpriseService.to_response(ent))


@router.put("/profile", response_model=ResponseModel[EnterpriseResponse])
def update_profile(
    data: EnterpriseUpdate,
    current_user=Depends(require_enterprise_owner_or_admin),
    db: Session = Depends(get_db),
):
    try:
        ent = EnterpriseService.update(db, current_user.enterprise_id, data)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return ResponseModel(data=EnterpriseService.to_response(ent), message="已更新")


@router.get("/members", response_model=ListResponse[UserResponse])
def list_members(
    params: MemberListParams = Depends(),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = UserService.list_members(db, current_user.enterprise_id, params)
    return ListResponse(
        total=total,
        page=params.page,
        page_size=params.page_size,
        items=[UserService.to_response(u) for u in items],
    )


@router.post("/members/invite", response_model=ResponseModel[UserResponse])
def invite_member(
    data: MemberInvite,
    current_user=Depends(require_enterprise_owner_or_admin),
    db: Session = Depends(get_db),
):
    try:
        user = UserService.invite_member(db, current_user.enterprise_id, current_user, data)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return ResponseModel(data=UserService.to_response(user), message="邀请成功（MVP 未发送邮件，用户可直接登录")


@router.patch("/members/{member_id}", response_model=ResponseModel[UserResponse])
def update_member(
    member_id: int,
    data: UserUpdate,
    current_user=Depends(require_enterprise_owner_or_admin),
    db: Session = Depends(get_db),
):
    try:
        user = UserService.update_user(db, current_user, member_id, data)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return ResponseModel(data=UserService.to_response(user), message="已更新")
