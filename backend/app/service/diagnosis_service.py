"""源诊断服务 — 探针 / 搜索 / 分析 / 源地图 / T0。"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.llm.gateway import chat, search, simple_prompt, simple_search
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# 并发控制：最多 5 条探针同时搜索
_SEARCH_SEMAPHORE = asyncio.Semaphore(5)


class DiagnosisService:
    """诊断服务 — 全静态方法，无状态。"""

    # ═══════════════════ 1. 生成探针 ═══════════════════

    @staticmethod
    async def generate_probes(
        enterprise_name: str,
        city: str = "",
        district: str = "",
        services: Optional[List[str]] = None,
        extra_context: str = "",
    ) -> List[str]:
        """用 LLM 生成 20-30 条探针问句。

        如果 A5 已生成探针（从 input_data 传入），直接复用，跳过 LLM 调用。
        """
        prompt = f"""请为以下美容门店生成 20-30 条"顾客在 AI 搜索引擎里可能输入的自然问句"（探针）。

门店信息：
- 店名：{enterprise_name}
- 城市：{city}
- 商圈：{district}
- 服务项目：{', '.join(services) if services else '未提供'}
- 补充信息：{extra_context or '无'}

要求：
1. 问句覆盖到店决策、项目咨询、成分疑虑、价格对比、售后评价 5 类场景
2. 每个问句包含地域限定词
3. 每条问句 10-30 字，自然搜索语言
4. 输出 JSON 数组：["问句1", "问句2", ...]
仅输出 JSON 数组，不要加 markdown。"""
        resp = await chat(simple_prompt(prompt, temperature=0.7, max_tokens=3000))
        if resp.ok:
            import json, re
            try:
                text = resp.content
                m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
                if m:
                    text = m.group(1)
                parsed = json.loads(text.strip())
                return parsed if isinstance(parsed, list) else [resp.content]
            except Exception:
                return [resp.content]
        # fallback
        probes = [
            f"{district}皮肤管理推荐哪家好",
            f"{city}{district}附近美容院哪个靠谱",
            f"{enterprise_name}怎么样 口碑",
        ]
        return probes

    # ═══════════════════ 2. 批量搜索 ═══════════════════

    @staticmethod
    async def _search_single_probe(
        db_factory,
        enterprise_id: int,
        probe: str,
        engine: str,
        batch_no: str,
    ) -> dict:
        """搜索单条探针 → 写入 search_results。"""
        from app.models.strategy import SearchResult

        async with _SEARCH_SEMAPHORE:
            try:
                resp = await search(simple_search(probe, engine=engine, timeout=200))
                citations_data = []
                if hasattr(resp, "citations"):
                    for c in resp.citations:
                        citations_data.append({
                            "url": c.url,
                            "title": c.title,
                            "summary": c.summary[:2000] if c.summary else "",
                            "site_name": c.site_name,
                            "publish_time": c.publish_time,
                        })

                db = db_factory()
                try:
                    sr = SearchResult(
                        enterprise_id=enterprise_id,
                        probe_query=probe,
                        engine=engine,
                        answer=resp.answer if hasattr(resp, "answer") else "",
                        citations=citations_data,
                        citation_count=len(citations_data),
                        diagnosis_batch_no=batch_no,
                        latency_ms=resp.latency_ms if hasattr(resp, "latency_ms") else 0,
                        error=resp.error if hasattr(resp, "error") else None,
                    )
                    db.add(sr)
                    db.commit()
                    return {"probe": probe, "ok": resp.ok, "citations": len(citations_data)}
                finally:
                    db.close()
            except Exception as e:
                logger.warning("[diagnosis] search probe failed: %s err=%s", probe[:50], e)
                return {"probe": probe, "ok": False, "error": str(e)}

    @staticmethod
    async def batch_search(
        db_factory,
        enterprise_id: int,
        probes: List[str],
        engines: Optional[List[str]] = None,
        batch_no: Optional[str] = None,
    ) -> List[dict]:
        """批量搜索：所有探针 × 豆包引擎，并发 ≤5。

        Args:
            db_factory: SessionLocal（lambda，每次调用创建新 session）
            enterprise_id: 租户 ID
            probes: 探针问句列表
            engines: 引擎列表，默认只搜豆包（非豆包跳过）
            batch_no: 批次号

        Returns:
            [{"probe": "...", "ok": True, "citations": 7}, ...]
        """
        if engines is None:
            engines = ["doubao"]  # 非豆包引擎跳过
        if batch_no is None:
            batch_no = datetime.utcnow().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]

        tasks = []
        for probe in probes:
            for engine in engines:
                tasks.append(
                    DiagnosisService._search_single_probe(
                        db_factory, enterprise_id, probe, engine, batch_no,
                    )
                )

        logger.info("[diagnosis] batch_search start probes=%s engines=%s", len(probes), engines)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤异常
        clean = []
        for r in results:
            if isinstance(r, Exception):
                clean.append({"probe": "?", "ok": False, "error": str(r)})
            else:
                clean.append(r)

        ok_count = sum(1 for r in clean if r.get("ok"))
        logger.info("[diagnosis] batch_search done total=%s ok=%s", len(clean), ok_count)
        return clean

    # ═══════════════════ 3. 分析 citations ═══════════════════

    @staticmethod
    async def analyze_from_citations(
        db: Session,
        enterprise_id: int,
        batch_no: str,
        enterprise_name: str = "",
    ) -> Dict[str, Any]:
        """从 search_results 中读取 citations，喂给 LLM 做分析。

        Returns:
            {
                "brand_mentioned": bool,
                "mention_context": str,
                "rank_estimate": int,
                "competitor_occupancy": [{"name": "...", "count": N, "platforms": [...]}],
                "pain_points": [{"point": "...", "severity": N, "evidence": "..."}],
                "scenarios": [{"title": "...", "query": "...", "intent": "...", "channel": "..."}],
            }
        """
        from app.models.strategy import SearchResult

        rows = (
            db.query(SearchResult)
            .filter(
                SearchResult.enterprise_id == enterprise_id,
                SearchResult.diagnosis_batch_no == batch_no,
            )
            .all()
        )

        if not rows:
            return {"brand_mentioned": False, "error": "无搜索数据"}

        # 汇总所有 citations
        all_citations = []
        for r in rows:
            for c in (r.citations or []):
                all_citations.append({
                    "probe": r.probe_query,
                    "answer": r.answer[:500] if r.answer else "",
                    **c,
                })

        # 截断：最多喂 50 条 citations 给 LLM
        cites_text = "\n---\n".join(
            f"[{c.get('site_name', '?')}] {c.get('title', '')}\n{c.get('summary', '')[:300]}"
            for c in all_citations[:50]
        )

        prompt = f"""你是美容行业市场分析师。以下是"{enterprise_name}"在 AI 搜索引擎中的真实搜索结果引用。

搜索引用（共 {len(all_citations)} 条，展示前 50 条）：
{cites_text}

请分析并输出 JSON 对象，字段：
- brand_mentioned: 我们的品牌是否被提及（true/false）
- mention_context: 如果被提及，描述上下文（正面/负面/中性，一句话）
- rank_estimate: 估计在搜索结果中的排名位置（1-100，1 为最佳）
- competitor_occupancy: 竞品出现情况，数组 [{{name, count, platforms}}]
- pain_points: 从搜索结果中推断的顾客痛点，数组 [{{point, severity(1-10), evidence}}]
- scenarios: 高频搜索场景，数组 [{{title, query, intent, channel}}]

仅输出 JSON 对象，不要加 markdown。"""
        resp = await chat(simple_prompt(prompt, temperature=0.4, max_tokens=3000))
        if resp.ok:
            import json, re
            try:
                text = resp.content
                m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
                if m:
                    text = m.group(1)
                return json.loads(text.strip())
            except Exception:
                pass
        return {"brand_mentioned": False, "error": str(resp.error) if not resp.ok else "JSON parse failed"}

    # ═══════════════════ 4. 信源地图 ═══════════════════

    @staticmethod
    def build_source_map(db: Session, enterprise_id: int, batch_no: str) -> dict:
        """从 search_results 聚合各平台引用分布。"""
        from app.models.strategy import SearchResult
        from collections import Counter

        rows = (
            db.query(SearchResult)
            .filter(
                SearchResult.enterprise_id == enterprise_id,
                SearchResult.diagnosis_batch_no == batch_no,
            )
            .all()
        )

        domain_counter = Counter()
        total = 0
        for r in rows:
            for c in (r.citations or []):
                site = c.get("site_name", "其他")
                domain_counter[site] += 1
                total += 1

        platforms = []
        for site, count in domain_counter.most_common():
            platforms.append({
                "domain": site,
                "site_name": site,
                "count": count,
                "weight": round(count / total, 3) if total > 0 else 0,
                "rankings": [],
                "gaps": [],
            })

        return {
            "total_citations": total,
            "total_probes": len(rows),
            "platforms": platforms,
            "top_domains": [p["domain"] for p in platforms[:5]],
        }

    # ═══════════════════ 5. 写 T0 基线 ═══════════════════

    @staticmethod
    def write_t0_baseline(
        db: Session,
        enterprise_id: int,
        batch_no: str,
        analysis: dict,
        source_map: dict,
    ) -> int:
        """将诊断结果写入 monitor_results 作为 T0 基线。

        Returns:
            写入的记录数
        """
        from app.models.monitor import MonitorResult
        from app.models.strategy import SearchResult

        rows = (
            db.query(SearchResult)
            .filter(
                SearchResult.enterprise_id == enterprise_id,
                SearchResult.diagnosis_batch_no == batch_no,
            )
            .all()
        )

        count = 0
        for r in rows:
            mr = MonitorResult(
                enterprise_id=enterprise_id,
                pool_type="probe",
                engine=r.engine,
                query=r.probe_query,
                mentioned=analysis.get("brand_mentioned", False),
                mention_snippet=analysis.get("mention_context", ""),
                position_rank=analysis.get("rank_estimate"),
                response_text=r.answer,
                competitor_mentions=analysis.get("competitor_occupancy", []),
                metrics={
                    "citation_count": r.citation_count,
                    "source_map": source_map,
                },
                baseline=True,
                run_at=datetime.utcnow(),
                batch_no=batch_no,
                metadata_={
                    "diagnosis_batch_no": batch_no,
                    "search_result_id": r.id,
                },
            )
            db.add(mr)
            count += 1

        db.commit()
        logger.info("[diagnosis] T0 written eid=%s count=%s", enterprise_id, count)
        return count

    # ═══════════════════ 全流程入口（Celery 调用） ═══════════════════

    @staticmethod
    async def run_full_diagnosis(
        enterprise_id: int,
        enterprise_name: str = "",
        city: str = "",
        district: str = "",
        services: Optional[List[str]] = None,
        extra_context: str = "",
        existing_probes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """全流程：探针 → 搜索 → 分析 → 信源地图 → T0。

        由 Celery 任务调用，不在 HTTP 请求中同步执行。
        """
        from app.core.db import SessionLocal

        batch_no = datetime.utcnow().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]

        # 1. 探针
        if existing_probes:
            probes = existing_probes
            logger.info("[diagnosis] reuse %s existing probes", len(probes))
        else:
            probes = await DiagnosisService.generate_probes(
                enterprise_name, city, district, services, extra_context,
            )
            logger.info("[diagnosis] generated %s probes", len(probes))

        # 2. 批量搜索
        search_results = await DiagnosisService.batch_search(
            SessionLocal, enterprise_id, probes, engines=["doubao"], batch_no=batch_no,
        )

        # 3. 分析
        db = SessionLocal()
        try:
            analysis = await DiagnosisService.analyze_from_citations(
                db, enterprise_id, batch_no, enterprise_name,
            )

            # 4. 信源地图
            source_map = DiagnosisService.build_source_map(db, enterprise_id, batch_no)

            # 5. T0 基线
            t0_count = DiagnosisService.write_t0_baseline(
                db, enterprise_id, batch_no, analysis, source_map,
            )

            return {
                "batch_no": batch_no,
                "probes_count": len(probes),
                "search_ok": sum(1 for r in search_results if r.get("ok")),
                "search_total": len(search_results),
                "analysis": analysis,
                "source_map": source_map,
                "t0_count": t0_count,
            }
        finally:
            db.close()
