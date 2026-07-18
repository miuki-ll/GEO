"""B6: Core/Probe profile · T1 baseline=false · delta · engines."""
from __future__ import annotations

from app.monitor_delta import (
    build_core_prompts,
    build_probe_prompts,
    compute_delta,
    normalize_engines,
    result_api_view,
)


def test_tb6_normalize_engines_follow_target():
    assert normalize_engines(["豆包", "DeepSeek"]) == ["doubao", "deepseek"]
    assert normalize_engines([]) == ["doubao", "deepseek"]


def test_tb6_core_probe_limits():
    handoff = {
        "diagnosis": {"probe_prompts": [f"q{i}" for i in range(25)]},
        "keywords": [{"keyword": f"k{i}"} for i in range(10)],
    }
    core = build_core_prompts(handoff, limit=20)
    assert len(core) == 20
    probe = build_probe_prompts(core, limit=10)
    assert len(probe) <= 10
    assert len(probe) >= 1


def test_tb6_compute_delta():
    t0 = [{"mentioned": False}, {"mentioned": False}]
    t1 = [{"mentioned": True}, {"mentioned": False}]
    d = compute_delta(t0, t1)
    assert d["mention_rate_t0"] == 0.0
    assert d["mention_rate_t1"] == 0.5
    assert d["delta_mention"] == 0.5
    assert d["waiting_for_a7"] is False


def test_tb6_delta_waiting_for_a7_when_no_t0():
    d = compute_delta([], [{"mentioned": True}])
    assert d["waiting_for_a7"] is True
    assert d["todo"] == "WAIT_FOR: A7"


def test_tb6_result_view_aliases():
    class R:
        id = 1
        enterprise_id = 9
        profile_id = 2
        pool_type = "core"
        engine = "doubao"
        query = "静安寺皮肤管理推荐"
        scenario_id = None
        mentioned = True
        mention_snippet = "x"
        trust_score = 0.8
        position_rank = 2
        baseline = False
        run_at = None
        batch_no = "b1"
        competitor_mentions = []
        metrics = {"hallucination": False, "citations": ["dianping.com"]}

    view = result_api_view(R())
    assert view["engine_code"] == "doubao"
    assert view["prompt"] == view["query"]
    assert view["brand_mentioned"] is True
    assert view["baseline"] is False
