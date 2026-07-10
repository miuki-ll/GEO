"""Agent trace persistence — LangSmith 双写本地审计。"""
from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models import AgentTrace


def write_agent_trace(
    db: Session,
    *,
    enterprise_id: int,
    agent_task_id: Optional[int],
    graph_name: str,
    step_idx: int = 0,
    step_name: Optional[str] = None,
    thought: Optional[str] = None,
    action: Optional[str] = None,
    observation: Optional[str] = None,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    latency_ms: int = 0,
    langsmith_run_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AgentTrace:
    row = AgentTrace(
        enterprise_id=enterprise_id,
        agent_task_id=agent_task_id,
        graph_name=graph_name,
        step_idx=step_idx,
        step_name=step_name,
        thought=thought,
        action=action,
        observation=observation,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        latency_ms=latency_ms,
        langsmith_run_id=langsmith_run_id,
        metadata_=metadata or {},
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
