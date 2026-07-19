"""关键词词库 schema — 四源汇聚 + 四层分类。"""
from datetime import datetime
from typing import Any, List, Optional

from pydantic import Field, model_validator

from app.schemas import BaseSchema, PaginationParams
from app.schemas._helpers import orm_to_metadata_dict


# ── 枚举 ──

KEYWORD_LAYERS = ["认知层", "选型层", "痛点层", "场景层"]
KEYWORD_SOURCES = ["RawInputs", "探针反推", "SEO API", "LLM生成", "手动"]


# ── 请求 ──

class KeywordCreate(BaseSchema):
    """手动添加关键词。"""
    phrase: str = Field(..., min_length=1, max_length=500)
    layer: str = Field(default="", max_length=20)
    source: str = Field(default="手动", max_length=20)
    lbs_tags: List[str] = Field(default_factory=list)
    keyword_type: str = Field(default="exact", max_length=30)
    pool_hint: str = Field(default="core", max_length=20)


class KeywordUpdate(BaseSchema):
    """编辑关键词。"""
    phrase: Optional[str] = Field(default=None, max_length=500)
    layer: Optional[str] = Field(default=None, max_length=20)
    source: Optional[str] = Field(default=None, max_length=20)
    lbs_tags: Optional[List[str]] = None
    keyword_type: Optional[str] = Field(default=None, max_length=30)
    pool_hint: Optional[str] = Field(default=None, max_length=20)
    status: Optional[str] = Field(default=None, max_length=20)


class KeywordListParams(PaginationParams):
    """关键词列表查询参数。"""
    layer: Optional[str] = None
    source: Optional[str] = None
    keyword_type: Optional[str] = None
    pool_hint: Optional[str] = None
    search: Optional[str] = None  # phrase 模糊搜索


class KeywordGenerateRequest(BaseSchema):
    """触发四源汇聚 + LLM 分类。"""
    pass  # 不需要额外参数，从 enterprise 和已有数据读取


# ── 响应 ──

class KeywordResponse(BaseSchema):
    """关键词响应。"""
    id: int
    enterprise_id: int
    phrase: str
    layer: str = ""
    source: str = "手动"
    lbs_tags: List[str] = Field(default_factory=list)
    keyword_type: str = "exact"
    pool_hint: str = "core"
    status: str = "draft"
    pain_cluster_id: Optional[str] = None
    metadata_: dict = Field(default_factory=dict, alias="metadata")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def _fix_orm(cls, data: Any) -> Any:
        # 避免把 SQLAlchemy Base.metadata（MetaData）当成业务 metadata
        return orm_to_metadata_dict(data)


class KeywordGenerateResponse(BaseSchema):
    """generate 任务响应。"""
    task_id: int
    message: str = "词库生成任务已启动"


class KeywordLayerSummary(BaseSchema):
    """四层汇总（给 B 侧 E 区用）。"""
    layer: str
    count: int
    keywords: List[str] = Field(default_factory=list)
