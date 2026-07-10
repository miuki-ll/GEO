from fastapi import APIRouter, Depends, Query

from mcp_server.auth import resolve_mcp_context
from mcp_server.tools import kb_fetch, kb_freshness_tool, kb_summary_tool

router = APIRouter(prefix="/mcp", tags=["MCP·只读工具"])


@router.get("/kb/fetch")
def http_kb_fetch(
    ctx: dict = Depends(resolve_mcp_context),
    fact_ids: list[int] | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
):
    return kb_fetch(enterprise_id=ctx["enterprise_id"], fact_ids=fact_ids, limit=limit)


@router.get("/kb/freshness")
def http_kb_freshness(ctx: dict = Depends(resolve_mcp_context)):
    return kb_freshness_tool(enterprise_id=ctx["enterprise_id"])


@router.get("/kb/summary")
def http_kb_summary(ctx: dict = Depends(resolve_mcp_context)):
    return kb_summary_tool(enterprise_id=ctx["enterprise_id"])
