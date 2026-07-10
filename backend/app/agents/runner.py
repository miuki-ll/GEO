"""Execute L2 graphs and sync AgentTask progress."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.agents.registry import get_graph_runner
from app.agents.state import AgentGraphState
from app.core.logging_config import get_logger
from app.service.agent_task_service import AgentTaskService

logger = get_logger(__name__)


async def run_graph(
    db: Session,
    enterprise_id: int,
    graph_name: str,
    input_data: Optional[Dict[str, Any]] = None,
    task_id: Optional[int] = None,
) -> AgentGraphState:
    runner = get_graph_runner(graph_name)
    if not runner:
        raise ValueError(f"Unknown graph: {graph_name}")

    state: AgentGraphState = {
        "enterprise_id": enterprise_id,
        "task_id": task_id,
        "graph_name": graph_name,
        "step": "start",
        "progress_pct": 0,
        "progress_message": "starting",
        "input_data": input_data or {},
        "output_data": {},
        "errors": [],
    }

    if task_id:
        AgentTaskService.update_progress(
            db, enterprise_id, task_id,
            status="running", progress_pct=5,
            progress_message="graph started",
            started_at=datetime.utcnow(),
        )

    try:
        state = await runner(state)
        if task_id:
            if state.get("errors"):
                AgentTaskService.complete_task(
                    db, enterprise_id, task_id,
                    output_data=state.get("output_data"),
                    error="; ".join(state["errors"]),
                )
            else:
                AgentTaskService.complete_task(
                    db, enterprise_id, task_id,
                    output_data=state.get("output_data"),
                )
        return state
    except Exception as e:
        logger.exception("run_graph failed graph=%s: %s", graph_name, e)
        if task_id:
            AgentTaskService.complete_task(db, enterprise_id, task_id, error=str(e))
        raise
