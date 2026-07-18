"""B4 内容检测链（固定链 · 无 ReAct）：5 项机审。

禁词业务路径只走 IndustryPack.get_industry_pack(...).forbidden_words()（TD-07）。
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence

TARGET_TYPE = "strategy_pack+content"

# 仅 APP_ENV=test 可见的兜底；生产/开发业务路径不得依赖此列表
_TEST_FALLBACK_WORDS = ["根治", "永不复发", "100%有效", "国家级"]


def resolve_forbidden_words(industry_pack_code: str = "beauty_local") -> tuple[List[str], bool]:
    """返回 (words, from_pack)。from_pack=False 仅允许测试兜底。"""
    code = (industry_pack_code or "beauty_local").strip() or "beauty_local"
    try:
        from app.agents.industry.registry import get_industry_pack

        pack = get_industry_pack(code)
        if pack:
            words = list(pack.forbidden_words() or [])
            if words:
                return words, True
    except Exception:
        pass

    # TD-07：A0 已交付后，业务路径不再用硬编码副本；仅 pytest/test 环境兜底
    try:
        from app.core.config import settings

        env = (getattr(settings, "APP_ENV", None) or "").strip().lower()
    except Exception:
        env = ""
    if env in ("test", "testing"):
        return list(_TEST_FALLBACK_WORDS), False
    raise ValueError(
        f"IndustryPack '{code}' forbidden_words 不可用；请确认 A0 registry 已注册该包"
    )


def check_fact_verify(
    body: str,
    facts: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """① 正文是否覆盖 fact_refs 关键片段。"""
    hits = []
    missing = []
    passed = True
    for f in facts:
        fid = int(f.get("id"))
        claim = (f.get("content") or "").strip()
        parts = [p for p in re.split(r"[，,。；;！!?？\s]", claim) if len(p) >= 2]
        hit = bool(claim) and (claim in body or any(p in body for p in parts[:5]))
        hits.append({"fact_id": fid, "hit": hit, "claim": claim[:80]})
        if not hit:
            missing.append(fid)
            passed = False
    if not facts:
        passed = False
        missing = []
    return {"ok": passed, "hits": hits, "missing_refs": missing}


def check_forbidden_words(text: str, words: Sequence[str]) -> Dict[str, Any]:
    """② 禁词：命中则 ok=False。

    契约（TD-04 定稿）：machine_review.forbidden_words 与其余四键同向 —
    **True = 该项通过（正文未命中禁词）**；False = 未通过（命中）。
    """
    found = []
    for w in words:
        if w and w in text:
            found.append(w)
    return {"ok": len(found) == 0, "hits": found}


def check_cross_validation(body: str, facts: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """③ 交叉验证（MOCK）：价格/NAP 类 Fact 至少各有一类可在正文出现，或无该类则跳过。"""
    cats = {str(f.get("category") or ""): f for f in facts}
    checks = []
    ok = True
    for cat in ("price", "nap"):
        f = cats.get(cat)
        if not f:
            checks.append({"category": cat, "required": False, "ok": True})
            continue
        content = f.get("content") or ""
        token = content[:6] if content else ""
        present = bool(token) and token in body
        checks.append({"category": cat, "required": True, "ok": present})
        if not present:
            ok = False
    return {"ok": ok, "checks": checks}


def check_entity_consistency(body: str, facts: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """④ 实体一致性：NAP 电话/地址片段若存在须一致出现。"""
    nap = next((f for f in facts if f.get("category") == "nap"), None)
    if not nap:
        return {"ok": True, "detail": "no_nap_fact"}
    content = nap.get("content") or ""
    phone = None
    m = re.search(r"(\d{3,4}-?\d{7,8}|\d{11})", content)
    if m:
        phone = m.group(1)
    ok = True
    detail = {}
    if phone:
        detail["phone"] = phone
        if phone not in body and phone.replace("-", "") not in body.replace("-", ""):
            # 信任背书段通常含 NAP；若整段 NAP 在正文则也算通过
            if content not in body:
                ok = False
                detail["phone_in_body"] = False
            else:
                detail["phone_in_body"] = True
        else:
            detail["phone_in_body"] = True
    else:
        detail["nap_in_body"] = content in body or content[:8] in body
        ok = bool(detail["nap_in_body"])
    return {"ok": ok, "detail": detail}


def check_rag_readability(rag_slices: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """⑤ RAG 可检索性：有切片；含 title/summary/keywords/body；结论宜前置。"""
    if not rag_slices:
        return {"ok": False, "reason": "empty_slices"}
    bad = []
    for i, sl in enumerate(rag_slices):
        for key in ("title", "summary", "keywords", "body", "chars"):
            if key not in sl:
                bad.append({"index": i, "missing": key})
        if not (sl.get("summary") or "").strip():
            bad.append({"index": i, "missing": "summary_empty"})
        if not (sl.get("keywords") or []):
            bad.append({"index": i, "missing": "keywords_empty"})
    first = rag_slices[0]
    lead_ok = "结论" in str(first.get("title") or "") or len(str(first.get("summary") or "")) >= 8
    ok = not bad and lead_ok
    return {"ok": ok, "issues": bad, "lead_ok": lead_ok}


def run_five_machine_reviews(
    *,
    body: str,
    title: str = "",
    facts: Sequence[Dict[str, Any]],
    rag_slices: Sequence[Dict[str, Any]],
    industry_pack_code: str = "beauty_local",
) -> Dict[str, Any]:
    """返回 handbook machine_review 五键 + 明细。"""
    text = f"{title}\n{body}"
    words, from_pack = resolve_forbidden_words(industry_pack_code)
    fv = check_fact_verify(body, facts)
    fw = check_forbidden_words(text, words)
    cv = check_cross_validation(body, facts)
    ec = check_entity_consistency(body, facts)
    rr = check_rag_readability(rag_slices)

    # TD-04 定稿：五键统一 True=该项通过；forbidden_words True=未命中禁词
    machine_review = {
        "fact_verify": bool(fv["ok"]),
        "forbidden_words": bool(fw["ok"]),
        "cross_validation": bool(cv["ok"]),
        "entity_consistency": bool(ec["ok"]),
        "rag_readability": bool(rr["ok"]),
    }
    all_ok = all(machine_review.values())
    return {
        "machine_review": machine_review,
        "passed": all_ok,
        "details": {
            "fact_verify": fv,
            "forbidden_words": fw,
            "cross_validation": cv,
            "entity_consistency": ec,
            "rag_readability": rr,
            "forbidden_from_pack": from_pack,
        },
        "target_type": TARGET_TYPE,
    }
