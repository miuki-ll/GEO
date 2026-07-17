"""B5 发布导出包（SEMI）与渠道模式推断。

AUTO 托管页真发 TODO(WAIT_FOR: A5)；此处生成 mock URL / Schema 占位。
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence


def infer_publish_mode(channel: str) -> str:
    c = (channel or "").strip().lower()
    if c in ("hosted", "ai托管页", "托管页", "ai_hosted"):
        return "auto"
    if c in ("xiaohongshu", "小红书", "xhs", "zhihu", "知乎", "wechat", "公众号"):
        return "semi"
    return "guided"


def build_semi_export_package(
    *,
    title: str,
    body: str,
    channel: str = "xiaohongshu",
    keywords: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """手册 SEMI 五字段：title/body/tags/cover_hint/steps。"""
    tags = list(keywords or [])
    if not tags:
        for tok in re.split(r"[\s，,。；;？?！!、#]+", title or ""):
            if len(tok) >= 2:
                tags.append(tok)
        tags = tags[:5] or ["皮肤管理", "敏感肌"]

    channel_l = (channel or "").lower()
    if "xiaohongshu" in channel_l or "小红书" in channel_l or "xhs" in channel_l:
        steps = [
            "打开小红书 APP",
            "点击发布笔记",
            "粘贴标题与正文",
            "上传封面图（按 cover_hint）",
            "添加话题标签后发布",
        ]
        cover_hint = "使用 VISIA 检测或门店实拍图，避免过度美颜"
    elif "zhihu" in channel_l or "知乎" in channel_l:
        steps = [
            "打开知乎",
            "创建回答/文章",
            "粘贴标题与正文",
            "补充引用与图片",
            "发布",
        ]
        cover_hint = "配一张项目对比或流程示意图"
    else:
        steps = [
            "打开对应平台 APP",
            "新建内容",
            "粘贴标题与正文",
            "上传图片",
            "发布并回填外链",
        ]
        cover_hint = "使用门店实景或项目过程图"

    # 正文截断到可粘贴长度（演示）
    body_text = (body or "").strip()
    if len(body_text) > 5000:
        body_text = body_text[:4997] + "..."

    return {
        "title": (title or "未命名")[:80],
        "body": body_text,
        "tags": tags[:8],
        "cover_hint": cover_hint,
        "steps": steps,
    }


def build_auto_mock_result(enterprise_id: int, task_id: int) -> Dict[str, Any]:
    """AUTO MOCK：假托管页 URL + Schema 片段。TODO(WAIT_FOR: A5)"""
    url = f"https://hosted.geo.local/e/{enterprise_id}/p/{task_id}"
    return {
        "published_url": url,
        "schema_snippet": {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "url": url,
            "name": "Demo 美业店",
        },
        "mock": True,
        "todo": "WAIT_FOR: A5",
    }


def publish_task_api_view(task: Any, asset: Any = None) -> Dict[str, Any]:
    meta = getattr(task, "metadata_", None) or {}
    if not isinstance(meta, dict):
        meta = {}
    title = None
    if asset is not None:
        title = getattr(asset, "title", None)
    return {
        "id": task.id,
        "content_asset_id": task.content_asset_id,
        "draft_id": task.content_asset_id,
        "channel": task.channel,
        "mode": task.mode,
        "status": task.status,
        "published_url": task.published_url,
        "published_id": task.published_id,
        "published_at": task.published_at.isoformat() if getattr(task, "published_at", None) else None,
        "retry_count": task.retry_count or 0,
        "fallback_semi": bool(task.fallback_semi),
        "error_message": task.error_message,
        "export_package": meta.get("export_package"),
        "auto_result": meta.get("auto_result"),
        "title": title or meta.get("title"),
        "enterprise_id": task.enterprise_id,
    }
