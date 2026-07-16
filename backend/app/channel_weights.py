"""Pure helpers for channel weight + MOCK five-zone payload (no FastAPI/DB imports)."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# TODO(WAIT_FOR: A-fixture) official four-file handoff from Developer A
_HANDOFF_BUNDLE = (
    Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "handoff_a_to_b" / "enterprise_bundle.json"
)


def compute_mixed_weight(model_weight: float, probe_weight: float) -> float:
    """Channel weight = internal model × 0.6 + probe map × 0.4."""
    return round(model_weight * 0.6 + probe_weight * 0.4, 6)


def load_handoff_mock() -> Dict[str, Any]:
    if not _HANDOFF_BUNDLE.is_file():
        return {}
    return json.loads(_HANDOFF_BUNDLE.read_text(encoding="utf-8"))


def build_five_zone_payload(handoff: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """MOCK five-zone draft — TODO(WAIT_FOR: A7+A8) for live diagnosis/keywords."""
    handoff = handoff if handoff is not None else load_handoff_mock()
    rankings = (handoff.get("diagnosis") or {}).get("source_map", {}).get("rankings") or []
    zhihu = next((r.get("weight", 0.15) for r in rankings if "zhihu" in str(r.get("domain", ""))), 0.15)
    dianping = next((r.get("weight", 0.2) for r in rankings if "dianping" in str(r.get("domain", ""))), 0.2)
    channel_rows = [
        {"name": "AI托管页", "model_weight": 0.40, "probe_weight": 0.10, "mode": "auto"},
        {"name": "小红书", "model_weight": 0.25, "probe_weight": 0.05, "mode": "semi"},
        {"name": "知乎", "model_weight": 0.10, "probe_weight": float(zhihu), "mode": "semi"},
        {"name": "大众点评", "model_weight": 0.15, "probe_weight": float(dianping), "mode": "guided"},
    ]
    channels = []
    for r in channel_rows:
        mixed = compute_mixed_weight(r["model_weight"], r["probe_weight"])
        channels.append(
            {
                **r,
                "mixed_weight": mixed,
                "weight": int(round(mixed * 100)),
                "scenario_count": 1,
            }
        )
    comps = (handoff.get("diagnosis") or {}).get("competitor_analysis") or []
    keywords = handoff.get("keywords") or []
    layers: Dict[str, List[Dict[str, Any]]] = {"选型层": [], "场景层": [], "痛点层": [], "认知层": []}
    for k in keywords:
        layers.setdefault(k.get("layer") or "选型层", []).append(k)
    scenarios = [
        {"id": "c1", "user_query": "敏感肌能不能做皮肤管理", "intent": "项目咨询", "channel": "hosted", "skill": "faq"},
        {"id": "c2", "user_query": "静安寺附近做脸哪家不推销", "intent": "到店决策", "channel": "xiaohongshu", "skill": "article"},
        {"id": "c3", "user_query": "XX皮肤管理和YY美容院怎么选", "intent": "选型对比", "channel": "zhihu", "skill": "comparison"},
    ]
    return {
        "persona": {
            "buyer_personas": [
                {
                    "role": "静安寺白领女性",
                    "age_range": [25, 35],
                    "pain_tags": ["敏感肌", "怕推销", "午休短"],
                    "decision_factors": ["口碑", "资质", "距离"],
                    "trust_triggers": ["VISIA报告", "评价带图"],
                }
            ],
            "content_layout_plan": [
                {
                    "persona": "敏感肌白领",
                    "content_type": "FAQ+场景推荐",
                    "channel": "小红书+知乎",
                    "cta": "预约小程序",
                }
            ],
        },
        "competitors": {
            "profiles": [
                {
                    "name": c.get("name"),
                    "type": c.get("type", "chain"),
                    "differentiation": c.get("differentiation") or "",
                    "strengths": c.get("strengths") or [],
                    "weaknesses": c.get("weaknesses") or [],
                }
                for c in comps
            ],
            "differentiation_brief": "透明价格 + 成分公开 + 1v1（MOCK）",
            "content_gaps": (handoff.get("diagnosis") or {}).get("source_map", {}).get("gaps") or [],
        },
        "scenarios": {"candidates": scenarios, "recommended_count": 3, "max": 5},
        "channels": channels,
        "keywords": {"layers": layers},
        "kb_freshness": {"warning": False, "updated_at": datetime.utcnow().isoformat() + "Z"},
    }
