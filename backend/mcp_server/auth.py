"""MCP API Key → enterprise_id（MVP：单 Key 绑定单租户）。"""
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings

_api_key_header = APIKeyHeader(name="X-MCP-API-Key", auto_error=False)


def resolve_mcp_context(api_key: str | None = Security(_api_key_header)) -> dict:
    if not settings.MCP_API_KEY:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "MCP 未配置 MCP_API_KEY")
    if not api_key or api_key != settings.MCP_API_KEY:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "无效的 MCP API Key")
    # MVP：env MCP_TENANT_ID 指定租户；V2 多 Key 映射表
    tenant_id = int(getattr(settings, "MCP_TENANT_ID", None) or __import__("os").getenv("MCP_TENANT_ID", "1"))
    return {"enterprise_id": tenant_id}
