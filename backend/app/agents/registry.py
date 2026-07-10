"""Graph registry — maps graph_name to runner."""
from __future__ import annotations

from typing import Awaitable, Callable, Dict

from app.agents.state import AgentGraphState

GraphRunner = Callable[[AgentGraphState], Awaitable[AgentGraphState]]

_REGISTRY: Dict[str, GraphRunner] = {}


def register_graph(name: str, runner: GraphRunner) -> None:
    _REGISTRY[name] = runner


def get_graph_runner(name: str) -> GraphRunner | None:
    return _REGISTRY.get(name)


def list_graphs() -> list[str]:
    return sorted(_REGISTRY.keys())
