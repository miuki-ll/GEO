"""Build onboarding graph and register runner."""
from app.agents.registry import register_graph
from app.agents.graphs.onboarding.nodes import run_onboarding_nodes

register_graph("onboarding", run_onboarding_nodes)
