"""入驻向导 — OnboardingRunRequest schema。"""
from typing import List, Optional

from pydantic import Field

from app.schemas.common import BaseSchema


class EnterpriseInfo(BaseSchema):
    """企业基本信息（Step 0 表单）。"""
    name: str = Field(..., min_length=1, max_length=200)
    industry: str = "beauty_local"
    license_no: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None


class BrandInfo(BaseSchema):
    """品牌信息。"""
    name: str = Field(..., min_length=1, max_length=200)
    differentiator: Optional[str] = None
    slogan: Optional[str] = None


class StoreInfo(BaseSchema):
    """门店信息。"""
    name: str = Field(..., min_length=1, max_length=200)
    city: Optional[str] = None
    district: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    business_hours: Optional[str] = None
    is_primary: bool = True


class ServiceInfo(BaseSchema):
    """服务项目。"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    price_hint: Optional[str] = None
    duration_minutes: Optional[int] = None


class SeedFact(BaseSchema):
    """种子 Fact。"""
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)


class OnboardingRunRequest(BaseSchema):
    """POST /user/onboarding/run 请求体 — 一次性提交全部入驻数据。"""
    enterprise: EnterpriseInfo
    brand: Optional[BrandInfo] = None
    stores: List[StoreInfo] = Field(default_factory=list)
    services: List[ServiceInfo] = Field(default_factory=list)
    competitors: List[str] = Field(default_factory=list)
    target_customers: str = ""
    raw_inputs: str = ""
    seed_facts: List[SeedFact] = Field(default_factory=list)
    target_engines: List[str] = Field(default_factory=list)
    search_enabled: bool = True
