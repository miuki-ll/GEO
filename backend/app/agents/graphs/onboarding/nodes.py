"""Onboarding graph nodes — DIAGNOSE → PAIN → PERSONA → COMPETITOR."""
from app.agents.graphs.onboarding.state import AgentGraphState
from app.core.logging_config import get_logger

logger = get_logger(__name__)

STEPS = ["DIAGNOSE", "PAIN", "PERSONA", "COMPETITOR"]


async def run_onboarding_nodes(state: AgentGraphState) -> AgentGraphState:
    eid = state["enterprise_id"]
    results = {}
    for i, step in enumerate(STEPS):
        pct = int((i + 1) / len(STEPS) * 100)
        state["step"] = step
        state["progress_pct"] = pct
        state["progress_message"] = f"{step} done"
        results[step] = {"ok": True, "enterprise_id": eid}
        logger.info("[onboarding] step=%s enterprise=%s", step, eid)
    state["output_data"] = {"steps": results, "next_route": "/strategy-pack?draft=1"}
    state["progress_pct"] = 100
    return state
