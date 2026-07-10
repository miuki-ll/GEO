"""
GEO MCP Server — 只读工具暴露（Model Context Protocol，模型上下文协议）。

启动：
  cd backend && python -m mcp_server.server

或 FastMCP（需 pip install fastmcp）：
  fastmcp run mcp_server/server.py
"""
from __future__ import annotations

import os
import sys

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.core.config import settings
from mcp_server.tools import kb_fetch, kb_freshness_tool, kb_summary_tool

try:
    from fastmcp import FastMCP
except ImportError:
    FastMCP = None  # type: ignore

mcp = FastMCP("GEO-Tools") if FastMCP else None


def _enterprise_id() -> int:
    return int(os.getenv("MCP_TENANT_ID", "1"))


if mcp is not None:

    @mcp.tool()
    def geo_kb_fetch(fact_ids: list[int] | None = None, limit: int = 10) -> dict:
        """只读：获取租户 KB Fact 列表或指定 ID。"""
        return kb_fetch(enterprise_id=_enterprise_id(), fact_ids=fact_ids, limit=limit)

    @mcp.tool()
    def geo_kb_freshness() -> dict:
        """只读：KB 新鲜度与 thin KB 检查。"""
        return kb_freshness_tool(enterprise_id=_enterprise_id())

    @mcp.tool()
    def geo_kb_summary() -> dict:
        """只读：KB 条目统计。"""
        return kb_summary_tool(enterprise_id=_enterprise_id())


def main():
    if mcp is None:
        print("请先安装: pip install fastmcp")
        print("只读工具已实现于 mcp_server/tools.py，可通过 HTTP 路由 /mcp 调用。")
        sys.exit(1)
    mcp.run(host=settings.MCP_HOST, port=settings.MCP_PORT)


if __name__ == "__main__":
    main()
