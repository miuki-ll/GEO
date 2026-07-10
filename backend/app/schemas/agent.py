"""Agent 任务 — 对齐 models/strategy.py AgentTask。"""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import Field

from app.schemas.common import BaseSchema, IDModel, TimestampResponse, PaginationParams


class AgentTaskBase(BaseSchema):
    task_type: str
    graph_name: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)


class AgentTaskCreate(AgentTaskBase):
    pass


class AgentTaskUpdate(BaseSchema):
    status: Optional[str] = None
    progress_pct: Optional[int] = None
    progress_message: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AgentTaskResponse(AgentTaskBase, IDModel, TimestampResponse):
    enterprise_id: int
    celery_task_id: Optional[str] = None
    status: str = "pending"
    progress_pct: int = 0
    progress_message: Optional[str] = None
    output_data: Dict[str, Any] = Field(default_factory=dict)
    trace_id: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AgentTaskListParams(PaginationParams):
    task_type: Optional[str] = None
    status: Optional[str] = None
