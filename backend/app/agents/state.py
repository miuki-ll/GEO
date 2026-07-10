"""LangGraph state definitions for L2 orchestrator."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class AgentGraphState(TypedDict, total=False):
    enterprise_id: int
    task_id: Optional[int]
    graph_name: str
    step: str
    progress_pct: int
    progress_message: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    errors: List[str]
    trace_id: Optional[str]
