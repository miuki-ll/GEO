"""ReAct Harness stub — ToolRegistry + LLM loop (MVP placeholder)."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from app.core.llm.gateway import chat, simple_prompt
from app.core.llm.schemas import LLMRequest

ToolFn = Callable[..., Any]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolFn] = {}

    def register(self, name: str, fn: ToolFn, description: str = "") -> None:
        self._tools[name] = fn

    def list_tools(self) -> List[str]:
        return sorted(self._tools.keys())

    async def run_tool(self, name: str, **kwargs: Any) -> Any:
        fn = self._tools.get(name)
        if not fn:
            raise KeyError(f"Tool not found: {name}")
        return fn(**kwargs)


async def react_step(prompt: str, *, system: Optional[str] = None) -> str:
    """Single ReAct LLM step via L1 Gateway."""
    req: LLMRequest = simple_prompt(prompt, system_prompt=system, temperature=0.3)
    resp = await chat(req)
    return resp.content if resp.ok else (resp.error or "")
