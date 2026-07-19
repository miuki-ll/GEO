"""入驻引导图节点 — DIAGNOSE → PAIN → PERSONA → COMPETITOR。"""

import asyncio
import json
import re

from app.agents.state import AgentGraphState
from app.core.llm.gateway import chat, search, simple_prompt, simple_search
from app.core.logging_config import get_logger
from app.core.sse import publish_progress, build_event

logger = get_logger(__name__)

# 每个节点占总进度的 25%
STEP_PCT = {0: 5, 1: 30, 2: 55, 3: 80, "done": 100}
STEP_MSG = {
    0: "生成探针问句中…",
    1: "分析痛点中…",
    2: "生成用户画像中…",
    3: "分析竞品中…",
}


def _parse_json(text: str) -> dict | list:
    """从 LLM 输出中提取 JSON — 兼容 ```json 包裹和纯文本。"""
    # 去掉 markdown 代码块
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        text = m.group(1)
    return json.loads(text.strip())


def _build_system_prompt() -> str:
    return (
        "你是一个美容行业市场分析专家。"
        "你的任务是根据给定的信息生成结构化分析结果。"
        "仅输出 JSON，不要加 markdown 代码块或额外解释。"
    )


# ═══════════════════ 节点 1：DIAGNOSE ═══════════════════

async def diagnose_node(state: AgentGraphState) -> AgentGraphState:
    """生成探针问句 + 可选联网搜索兜底。

    输入：品类/商圈/店名（从 input_data 提取）
    输出：state["probes"] + state["citations"] + state["search_used"]
    """
    inp = state.get("input_data", {})
    enterprise_name = (
        (inp.get("enterprise") or {}).get("name", "")
        or (inp.get("brand") or {}).get("name", "")
    )
    store = (inp.get("stores") or [{}])[0] if inp.get("stores") else {}
    city = store.get("city", "")
    district = store.get("district", "")
    address = store.get("address", "")
    industry = inp.get("industry", "beauty_local")
    services = inp.get("services", [])
    service_names = [s.get("name", "") for s in services]
    search_enabled = inp.get("search_enabled", True)

    # 构建 LLM prompt
    prompt = f"""请为以下美容门店生成 20-30 条"顾客在 AI 搜索引擎里可能输入的自然问句"（探针）。

门店信息：
- 品类：{industry}（生美/皮肤管理）
- 店名：{enterprise_name}
- 城市：{city}
- 商圈：{district}
- 地址：{address}
- 服务项目：{', '.join(service_names) if service_names else '未提供'}

要求：
1. 问句覆盖到店决策、项目咨询、成分疑虑、价格对比、售后评价 5 类场景
2. 每个问句包含地域限定词（如"{district}"）
3. 每条问句 10-30 字，自然搜索语言
4. 输出 JSON 数组：["问句1", "问句2", ...]
"""
    resp = await chat(simple_prompt(prompt, temperature=0.7, max_tokens=3000))
    if not resp.ok:
        state["errors"] = state.get("errors", []) + [f"DIAGNOSE chat 失败: {resp.error}"]
        # 兜底：用模板生成几条基本探针
        probes = [
            f"{district}皮肤管理推荐哪家好",
            f"{city}{district}附近美容院哪个靠谱",
            f"{enterprise_name}怎么样 口碑",
        ]
    else:
        try:
            parsed = _parse_json(resp.content)
            probes = parsed if isinstance(parsed, list) else [resp.content]
        except Exception:
            probes = [resp.content]

    # 可选：联网搜索兜底（取 3-5 条关键探针并行搜索）
    citations = []
    search_used = False
    if search_enabled:
        # 挑 4 条代表性探针（首尾中样 + 最长的那条）
        key_indices = [0, len(probes) // 2, len(probes) - 1]
        if len(probes) > 3:
            key_indices.append(len(probes) // 4)
        key_probes = [probes[i] for i in key_indices if i < len(probes)]

        try:
            # 并行搜索
            results = await asyncio.gather(
                *[search(simple_search(q, timeout=200)) for q in key_probes],
                return_exceptions=True,
            )
            for r in results:
                if isinstance(r, Exception):
                    logger.warning("[DIAGNOSE] search probe failed: %s", r)
                    continue
                if hasattr(r, "citations"):
                    for c in r.citations:
                        citations.append({
                            "url": c.url,
                            "title": c.title,
                            "summary": c.summary[:500],
                            "site_name": c.site_name,
                        })
            # 去重（按 url）
            seen = set()
            uniq = []
            for c in citations:
                if c["url"] not in seen:
                    seen.add(c["url"])
                    uniq.append(c)
            citations = uniq[:20]  # 最多保留 20 条
            search_used = len(citations) > 0
            logger.info("[DIAGNOSE] search got %s citations", len(citations))
        except Exception as e:
            logger.warning("[DIAGNOSE] search phase failed: %s", e)

    state["probes"] = probes
    state["citations"] = citations
    state["search_used"] = search_used
    state["step"] = "PAIN"
    state["progress_pct"] = STEP_PCT[1]
    state["progress_message"] = STEP_MSG[1]
    if state.get("task_id"):
        publish_progress(state["task_id"], build_event(
            progress_pct=STEP_PCT[1], progress_message=STEP_MSG[1], step="PAIN",
        ))
    return state


# ═══════════════════ 节点 2：PAIN ═══════════════════

async def pain_node(state: AgentGraphState) -> AgentGraphState:
    """分析痛点。

    输入：raw_inputs + 服务项目 + citations 摘要
    输出：state["pain_points"]
    """
    inp = state.get("input_data", {})
    raw_inputs = inp.get("raw_inputs", "")
    services = inp.get("services", [])
    service_names = [s.get("name", "") for s in services]
    citations = state.get("citations", [])
    search_used = state.get("search_used", False)

    # 构建上下文
    context_parts = []
    if raw_inputs.strip():
        context_parts.append(f"店主自述：\n{raw_inputs}")
    if service_names:
        context_parts.append(f"服务项目：{', '.join(service_names)}")
    if citations:
        cites_text = "\n".join(
            f"- [{c['site_name']}] {c['title']}: {c['summary'][:200]}"
            for c in citations[:10]
        )
        context_parts.append(f"联网搜索引用（{'真实数据' if search_used else '未使用搜索'}）：\n{cites_text}")

    if not context_parts and not service_names:
        state["pain_points"] = [{"point": "数据不足，无法分析痛点", "severity": 0, "evidence": ""}]
    else:
        prompt = f"""根据以下信息，分析该美容门店的市场痛点。

{chr(10).join(context_parts)}

输出 JSON 数组，每条包含：
- point: 痛点描述（一句话）
- severity: 严重程度 1-10
- evidence: 判断依据（引用自述或搜索结果）

仅输出 JSON 数组，不要加 markdown。"""
        resp = await chat(simple_prompt(prompt, temperature=0.5, max_tokens=2000))
        try:
            state["pain_points"] = _parse_json(resp.content) if resp.ok else []
        except Exception:
            state["pain_points"] = []

    state["step"] = "PERSONA"
    state["progress_pct"] = STEP_PCT[2]
    state["progress_message"] = STEP_MSG[2]
    if state.get("task_id"):
        publish_progress(state["task_id"], build_event(
            progress_pct=STEP_PCT[2], progress_message=STEP_MSG[2], step="PERSONA",
        ))
    return state


# ═══════════════════ 节点 3：PERSONA ═══════════════════

async def persona_node(state: AgentGraphState) -> AgentGraphState:
    """生成用户画像。

    输入：客群描述 + PAIN 输出 + citations
    输出：state["persona"]
    """
    inp = state.get("input_data", {})
    target_customers = inp.get("target_customers", "")
    pain_points = state.get("pain_points", [])
    citations = state.get("citations", [])

    # 从 IndustryPack 获取默认画像模板作为 fallback
    from app.agents.industry.registry import get_industry_pack
    pack = get_industry_pack(inp.get("industry", "beauty_local"))
    default_persona = pack.default_persona() if pack else {}

    pain_text = "\n".join(
        f"- {p.get('point', p)}" for p in (pain_points or [])[:5]
    ) if pain_points else "（未分析）"

    cites_text = "\n".join(
        f"- [{c['site_name']}] {c['title']}"
        for c in citations[:8]
    ) if citations else "（未使用搜索）"

    prompt = f"""为以下美容门店生成目标客群画像。

客群描述：{target_customers or '未提供，请根据行业特征推断'}
已识别痛点：
{pain_text}

搜索引用（了解市场环境）：
{cites_text}

行业默认画像（参考，可覆盖）：
{json.dumps(default_persona, ensure_ascii=False)}

输出 JSON 对象，字段：
- age_range: [最小年龄, 最大年龄]
- genders: ["性别1", ...]
- cities: ["城市/区域", ...]
- core_needs: ["核心需求1", ...]  (4-6个)
- decision_factors: ["决策因子1", ...]  (按重要性排序)
- typical_queries: ["典型搜索问句1", ...]  (5-8条)

仅输出 JSON 对象，不要加 markdown。"""
    resp = await chat(simple_prompt(prompt, temperature=0.6, max_tokens=2000))
    if resp.ok:
        try:
            state["persona"] = _parse_json(resp.content)
        except Exception:
            state["persona"] = default_persona
    else:
        state["persona"] = default_persona
        state["errors"] = state.get("errors", []) + [f"PERSONA chat 失败: {resp.error}"]

    state["step"] = "COMPETITOR"
    state["progress_pct"] = STEP_PCT[3]
    state["progress_message"] = STEP_MSG[3]
    if state.get("task_id"):
        publish_progress(state["task_id"], build_event(
            progress_pct=STEP_PCT[3], progress_message=STEP_MSG[3], step="COMPETITOR",
        ))
    return state


# ═══════════════════ 节点 4：COMPETITOR ═══════════════════

async def competitor_node(state: AgentGraphState) -> AgentGraphState:
    """竞品分析。

    输入：用户填的竞品名 + citations 中出现的品牌
    输出：state["competitors"]
    """
    inp = state.get("input_data", {})
    user_competitors = inp.get("competitors", [])
    citations = state.get("citations", [])
    enterprise_name = (inp.get("enterprise") or {}).get("name", "")

    # 从 citations 中提取可能出现的品牌名（给 LLM 做参考）
    cite_titles = "\n".join(
        f"- [{c['site_name']}] {c['title']}: {c['summary'][:150]}"
        for c in citations[:10]
    ) if citations else "（无搜索数据）"

    user_comps = ", ".join(user_competitors) if user_competitors else "未提供"

    prompt = f"""为"{enterprise_name}"做竞品分析。

用户指定的竞品：{user_comps}

搜索结果中出现的相关品牌/门店（用于推断竞品）：
{cite_titles}

要求：
1. 如果用户未指定竞品，从搜索结果中提取 2-4 个相关品牌
2. 输出 JSON 数组，每条包含：
   - name: 竞品名称
   - type: "chain"（连锁）/ "local"（本地）/ "studio"（工作室）
   - ai_mention_rate: 估计的 AI 搜索结果中出现频率 0-100
   - strengths: ["优势1", ...]
   - weaknesses: ["劣势1", ...]
   - differentiator: 我们相对于这个竞品的差异化优势（一句话）

仅输出 JSON 数组，不要加 markdown。"""
    resp = await chat(simple_prompt(prompt, temperature=0.5, max_tokens=2500))
    if resp.ok:
        try:
            state["competitors"] = _parse_json(resp.content)
        except Exception:
            state["competitors"] = []
    else:
        state["competitors"] = []
        state["errors"] = state.get("errors", []) + [f"COMPETITOR chat 失败: {resp.error}"]

    state["step"] = "done"
    state["progress_pct"] = STEP_PCT["done"]
    state["progress_message"] = "入驻分析完成"
    if state.get("task_id"):
        publish_progress(state["task_id"], build_event(
            progress_pct=STEP_PCT["done"],
            progress_message="入驻分析完成",
            step="done",
            status="completed",
            next_route="/strategy-pack?draft=1",
        ))
    return state


# ═══════════════════ 编排入口 ═══════════════════

async def run_onboarding_nodes(state: AgentGraphState) -> AgentGraphState:
    """DIAGNOSE → PAIN → PERSONA → COMPETITOR 顺序执行。

    由 runner.run_graph() 调用，runner 负责 AgentTask 生命周期。
    """
    state["step"] = "DIAGNOSE"
    state["progress_pct"] = STEP_PCT[0]
    state["progress_message"] = STEP_MSG[0]
    if state.get("task_id"):
        publish_progress(state["task_id"], build_event(
            progress_pct=STEP_PCT[0], progress_message=STEP_MSG[0], step="DIAGNOSE",
        ))

    state = await diagnose_node(state)
    state = await pain_node(state)
    state = await persona_node(state)
    state = await competitor_node(state)

    # 汇总 output_data
    state["output_data"] = {
        "probes": state.get("probes", []),
        "pain_points": state.get("pain_points", []),
        "persona": state.get("persona", {}),
        "competitors": state.get("competitors", []),
        "citations": state.get("citations", []),
        "search_used": state.get("search_used", False),
        "next_route": "/strategy-pack?draft=1",
    }

    logger.info("[onboarding] complete eid=%s probes=%s pains=%s",
                state["enterprise_id"],
                len(state.get("probes", [])),
                len(state.get("pain_points", [])))
    return state
