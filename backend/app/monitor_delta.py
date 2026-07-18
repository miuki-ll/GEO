"""B6 监测：T0/T1 Δ 与引擎归一（纯函数，便于单测）。

T0（baseline=true）由 A7 写；MOCK 可用 fixture 假 T0。
T1（baseline=false）由 B 写。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

# 引擎别名 → 契约枚举
_ENGINE_ALIASES = {
    "豆包": "doubao",
    "doubao": "doubao",
    "deepseek": "deepseek",
    "DeepSeek": "deepseek",
    "kimi": "kimi",
    "Kimi": "kimi",
    "文心": "wenxin",
    "文心一言": "wenxin",
    "wenxin": "wenxin",
}

DEFAULT_ENGINES = ["doubao", "deepseek"]


def normalize_engine(code: str) -> str:
    c = (code or "").strip()
    return _ENGINE_ALIASES.get(c, c.lower() or "doubao")


def normalize_engines(raw: Optional[Sequence[str]]) -> List[str]:
    out: List[str] = []
    for e in raw or []:
        n = normalize_engine(str(e))
        if n and n not in out:
            out.append(n)
    return out or list(DEFAULT_ENGINES)


def mention_rate(rows: Sequence[Any]) -> float:
    """rows: objects/dicts with mentioned / brand_mentioned."""
    if not rows:
        return 0.0
    hits = 0
    for r in rows:
        if isinstance(r, dict):
            m = r.get("mentioned")
            if m is None:
                m = r.get("brand_mentioned")
        else:
            m = getattr(r, "mentioned", None)
        if m:
            hits += 1
    return round(hits / len(rows), 4)


def compute_delta(t0_rows: Sequence[Any], t1_rows: Sequence[Any]) -> Dict[str, Any]:
    """返回 handbook KPI 片段：mention_rate_t0/t1 + delta_mention。

    TODO(WAIT_FOR: A7) 真 T0；无 T0 时 t0=0 并标记 waiting_for_a7。
    """
    r0 = mention_rate(t0_rows)
    r1 = mention_rate(t1_rows)
    waiting = len(t0_rows) == 0
    return {
        "mention_rate_t0": r0,
        "mention_rate_t1": r1,
        "delta_mention": round(r1 - r0, 4),
        "t0_samples": len(t0_rows),
        "t1_samples": len(t1_rows),
        "waiting_for_a7": waiting,
        "todo": "WAIT_FOR: A7" if waiting else None,
    }


def build_core_prompts(handoff: Dict[str, Any], limit: int = 20) -> List[str]:
    diag = handoff.get("diagnosis") or {}
    prompts = list(diag.get("probe_prompts") or [])
    for k in handoff.get("keywords") or []:
        kw = (k.get("keyword") if isinstance(k, dict) else None) or ""
        if kw and kw not in prompts:
            prompts.append(kw)
    return prompts[:limit]


def build_probe_prompts(core: Sequence[str], limit: int = 10) -> List[str]:
    """Probe：在 Core 基础上加长尾变体，≤10。"""
    extras = []
    for p in core:
        extras.append(f"{p} 附近")
        extras.append(f"平价 {p}")
    # 去重保序
    seen = set(core)
    out: List[str] = []
    for e in extras:
        if e not in seen:
            seen.add(e)
            out.append(e)
        if len(out) >= limit:
            break
    return out[:limit]


def result_api_view(row: Any) -> Dict[str, Any]:
    """API 视图：ORM 字段 + 手册别名（engine_code / prompt / brand_mentioned）。"""
    base = bool(getattr(row, "baseline", False))
    return {
        "id": row.id,
        "enterprise_id": row.enterprise_id,
        "profile_id": getattr(row, "profile_id", None),
        "pool_type": row.pool_type,
        "engine": row.engine,
        "engine_code": normalize_engine(row.engine or ""),
        "query": row.query,
        "prompt": row.query,
        "scenario_id": row.scenario_id,
        "mentioned": bool(row.mentioned),
        "brand_mentioned": bool(row.mentioned),
        "mention_snippet": row.mention_snippet,
        "trust_score": row.trust_score,
        "position_rank": row.position_rank,
        "rank": row.position_rank,
        "hallucination": bool((row.metrics or {}).get("hallucination")) if isinstance(getattr(row, "metrics", None), dict) else False,
        "citations": (row.metrics or {}).get("citations") if isinstance(getattr(row, "metrics", None), dict) else [],
        "baseline": base,
        "run_at": row.run_at.isoformat() if getattr(row, "run_at", None) else None,
        "batch_no": row.batch_no,
        "competitor_mentions": row.competitor_mentions or [],
    }
