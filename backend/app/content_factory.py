"""B3 内容工厂：固定链 kb_fetch → LLM(stub) → 7 段式 → RAG 切片。

真接：TODO(WAIT_FOR: A2+A3) — fact_refs 指向真实 kb_facts；正文经 gateway.chat()。
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence

# 7 段式（结论前置 + 场景/事实/方案/信任/风险/行动）
SEVEN_SEGMENT_KEYS = (
    "结论前置",
    "场景共鸣",
    "事实依据",
    "方案步骤",
    "信任背书",
    "风险说明",
    "行动号召",
)


def _fixture_kb_facts() -> List[Dict[str, Any]]:
    """MOCK：优先官方 kb_facts.json；否则 bundle。TODO(WAIT_FOR: A2) 真库。"""
    from app.channel_weights import load_handoff_mock

    return list(load_handoff_mock().get("kb_facts") or [])


def load_fixture_kb_facts() -> List[Dict[str, Any]]:
    return _fixture_kb_facts()


def kb_fetch(
    *,
    fact_ids: Optional[Sequence[int]] = None,
    db_facts: Optional[Sequence[Any]] = None,
) -> List[Dict[str, Any]]:
    """固定链第 1 步：拉取 Fact。优先 DB 行；否则 fixture。"""
    if db_facts:
        rows = []
        for f in db_facts:
            rows.append(
                {
                    "id": int(f.id),
                    "title": getattr(f, "title", "") or "",
                    "content": getattr(f, "content", "") or "",
                    "category": getattr(f, "category", "") or "",
                }
            )
        if fact_ids:
            want = set(int(x) for x in fact_ids)
            rows = [r for r in rows if r["id"] in want]
        if rows:
            return rows

    fixture = load_fixture_kb_facts()
    if fact_ids:
        want = set(int(x) for x in fact_ids)
        filtered = [r for r in fixture if int(r["id"]) in want]
        return filtered or fixture
    return fixture


def build_seven_segments(
    user_query: str,
    facts: Sequence[Dict[str, Any]],
    *,
    channel: str = "hosted",
    skill: str = "faq",
) -> Dict[str, str]:
    """固定链第 2 步：7 段式填充（LLM stub）。TODO(WAIT_FOR: A3 chat())"""
    fact_lines = "\n".join(
        f"- [{f.get('id')}] {f.get('title', '')}: {f.get('content', '')}" for f in facts
    ) or "- （暂无 Fact，使用占位）"
    nap = next((f for f in facts if f.get("category") == "nap"), None)
    price = next((f for f in facts if f.get("category") == "price"), None)
    service = next((f for f in facts if f.get("category") == "service"), None)

    conclusion = f"针对「{user_query}」：可以先做检测再护理，价格与门店信息以门店公示为准。"
    if service:
        conclusion = f"针对「{user_query}」：{service.get('content')}。"

    return {
        "结论前置": conclusion,
        "场景共鸣": f"很多到店客人会问同样的问题：{user_query}。我们按真实项目与检测流程说明，不夸大功效。",
        "事实依据": f"以下内容来自已核验 Fact（[fact_ref]）：\n{fact_lines}",
        "方案步骤": (
            "1. 到店沟通诉求与皮肤状态\n"
            "2. 必要时做 VISIA / 基础检测\n"
            "3. 按检测结果选护理项目与频次\n"
            f"4. 渠道形态：{channel} / Skill：{skill}"
        ),
        "信任背书": (
            f"门店信息：{nap.get('content') if nap else '详见门店页面'}。"
            f"参考价：{price.get('content') if price else '到店确认'}。"
        ),
        "风险说明": "个体差异存在；敏感肌需评估后再护理；本文不构成医疗建议，不使用绝对化功效承诺。",
        "行动号召": "可先预约咨询或到托管页留下联系方式，由顾问一对一说明项目与注意事项。",
    }


def render_seven_body(segments: Dict[str, str]) -> str:
    parts = []
    for key in SEVEN_SEGMENT_KEYS:
        text = segments.get(key, "").strip()
        parts.append(f"### {key}\n{text}")
    return "\n\n".join(parts)


def build_rag_slices(
    body: str,
    *,
    keywords: Optional[Sequence[str]] = None,
    min_chars: int = 300,
    max_chars: int = 800,
) -> List[Dict[str, Any]]:
    """生成时自动 RAG 切片：独立标题+摘要+关键词；目标 300–800 字/块。"""
    keywords = list(keywords or [])
    # 按三级标题切块
    chunks = re.split(r"(?=^### )", body, flags=re.M)
    chunks = [c.strip() for c in chunks if c.strip()]
    if not chunks:
        chunks = [body.strip()]

    slices: List[Dict[str, Any]] = []
    buf = ""
    buf_title = "正文切片"

    def flush(title: str, text: str) -> None:
        text = text.strip()
        if not text:
            return
        # 过短则仍输出（MOCK）；过长则硬切
        pieces = []
        if len(text) <= max_chars:
            pieces = [text]
        else:
            start = 0
            while start < len(text):
                pieces.append(text[start : start + max_chars])
                start += max_chars
        for i, piece in enumerate(pieces):
            lead = piece[:200]
            title_i = title if i == 0 else f"{title}（续{i + 1}）"
            summary = lead if len(lead) <= 120 else lead[:117] + "..."
            slices.append(
                {
                    "title": title_i,
                    "summary": summary,
                    "keywords": keywords[:8],
                    "body": piece,
                    "chars": len(piece),
                }
            )

    for ch in chunks:
        m = re.match(r"^###\s+(.+?)\n([\s\S]*)$", ch)
        title = m.group(1).strip() if m else "正文切片"
        text = m.group(2).strip() if m else ch
        if buf and len(buf) + len(text) < min_chars:
            buf = f"{buf}\n\n### {title}\n{text}"
            continue
        if buf:
            flush(buf_title, buf)
            buf = ""
        if len(text) < min_chars:
            buf = f"### {title}\n{text}"
            buf_title = title
        else:
            flush(title, text)

    if buf:
        flush(buf_title, buf)

    if not slices and body.strip():
        flush("全文", body.strip())
    return slices


def run_fixed_chain(
    *,
    user_query: str,
    channel: str = "hosted",
    skill: str = "faq",
    fact_ids: Optional[Sequence[int]] = None,
    db_facts: Optional[Sequence[Any]] = None,
    extra_keywords: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """
    SkillRuntime 固定链（无 ReAct）：
    kb_fetch → 7 段式 stub → RAG 切片。
    """
    facts = kb_fetch(fact_ids=fact_ids, db_facts=db_facts)
    refs = [int(f["id"]) for f in facts]
    segments = build_seven_segments(user_query, facts, channel=channel, skill=skill)
    body = render_seven_body(segments)
    kws = list(extra_keywords or [])
    for f in facts:
        if f.get("title"):
            kws.append(str(f["title"]))
    # 从问句抽简单词
    for tok in re.split(r"[\s，,？?！!、]+", user_query):
        if len(tok) >= 2:
            kws.append(tok)
    # 去重保序
    seen = set()
    keywords = []
    for k in kws:
        if k not in seen:
            seen.add(k)
            keywords.append(k)

    slices = build_rag_slices(body, keywords=keywords)
    title = user_query if len(user_query) <= 80 else user_query[:77] + "..."
    return {
        "title": title,
        "body": body,
        "fact_refs": refs,
        "rag_slices": slices,
        "seven_segments": segments,
        "channel": channel,
        "skill": skill,
        # stub 机审占位；B4 写真检测链。五键 True=通过（含 forbidden_words）
        "machine_review": {
            "fact_verify": True,
            "forbidden_words": True,
            "cross_validation": True,
            "entity_consistency": True,
            "rag_readability": True,
        },
        "status": "ready",
        "mock": True,  # TODO(WAIT_FOR: A2+A3)
    }


def draft_api_view(asset: Any) -> Dict[str, Any]:
    """把 ORM ContentAsset 转成手册 §B3 草稿形状。"""
    meta = getattr(asset, "metadata_", None) or {}
    if not isinstance(meta, dict):
        meta = {}
    body = getattr(asset, "content", "") or ""
    return {
        "id": asset.id,
        "scenario_id": asset.scenario_id,
        "channel": asset.channel,
        "skill": asset.skill,
        "title": asset.title,
        "body": body,
        "content": body,
        "fact_refs": list(getattr(asset, "fact_refs", None) or []),
        "rag_slices": list(meta.get("rag_slices") or []),
        "machine_review": meta.get("machine_review")
        or {
            "fact_verify": bool(getattr(asset, "fact_verify_pass", None)),
            "forbidden_words": bool(getattr(asset, "compliance_pass", True)),
            "cross_validation": True,
            "entity_consistency": True,
            "rag_readability": bool(meta.get("rag_slices")),
        },
        "status": asset.status,
        "human_review_status": getattr(asset, "human_review_status", None),
    }
