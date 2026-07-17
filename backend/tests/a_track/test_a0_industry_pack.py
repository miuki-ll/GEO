"""A0 IndustryPack 测试 — 基类加载 + beauty_local 规则簿六维数据验证。

用例对照 G-L3-开发者A任务手册.md §11.3：
  T-A0-01 ~ T-A0-06
"""
import pytest


# ── T-A0-01：get_industry_pack("beauty_local") 不抛异常，code 正确 ──
def test_load_beauty_local_pack():
    """加载 beauty_local 行业包，验证 code 和 name。"""
    from app.agents.industry.registry import get_industry_pack

    pack = get_industry_pack("beauty_local")
    assert pack is not None, "get_industry_pack('beauty_local') 返回 None"
    assert pack.code == "beauty_local", f"code 应为 'beauty_local'，实际: {pack.code}"
    assert pack.name == "生美本地 · 皮肤管理", f"name 不匹配: {pack.name}"


# ── T-A0-02：forbidden_words() 返回非空 List[str] ──
def test_forbidden_words():
    """禁词列表：≥10 条，全为 str。"""
    from app.agents.industry.registry import get_industry_pack

    pack = get_industry_pack("beauty_local")
    words = pack.forbidden_words()
    assert isinstance(words, list), f"forbidden_words 应返回 list，实际: {type(words)}"
    assert len(words) >= 10, f"禁词应 ≥10 条，实际: {len(words)}"
    for w in words:
        assert isinstance(w, str), f"禁词元素应为 str，实际: {type(w)}: {w}"


# ── T-A0-03：channel_weights() 返回 List[dict]，每项含 name/weight ──
def test_channel_weights():
    """渠道权重列表：5 个渠道，每项含 name 和 weight。"""
    from app.agents.industry.registry import get_industry_pack

    pack = get_industry_pack("beauty_local")
    channels = pack.channel_weights()
    assert isinstance(channels, list), "channel_weights 应返回 list"
    assert len(channels) == 5, f"渠道应为 5 个，实际: {len(channels)}"
    for ch in channels:
        assert isinstance(ch, dict), f"渠道项应为 dict，实际: {type(ch)}"
        assert "name" in ch, f"渠道项缺 'name': {ch}"
        assert "weight" in ch, f"渠道项缺 'weight': {ch}"
        assert isinstance(ch["weight"], (int, float)), f"weight 应为数字: {ch['weight']}"


# ── T-A0-04：default_persona() 返回 dict，含角色/年龄段/痛点字段 ──
def test_default_persona():
    """默认画像：含 age_range / core_needs / decision_factors / typical_queries。"""
    from app.agents.industry.registry import get_industry_pack

    pack = get_industry_pack("beauty_local")
    persona = pack.default_persona()
    assert isinstance(persona, dict), f"default_persona 应返回 dict，实际: {type(persona)}"

    # 必含字段
    assert "age_range" in persona, f"persona 缺 'age_range': {list(persona.keys())}"
    assert "core_needs" in persona, f"persona 缺 'core_needs'"
    assert "decision_factors" in persona, f"persona 缺 'decision_factors'"
    assert "typical_queries" in persona, f"persona 缺 'typical_queries'"

    # 类型校验
    assert isinstance(persona["age_range"], list), "age_range 应为 list"
    assert len(persona["age_range"]) == 2, f"age_range 应为 [min, max]，实际长度: {len(persona['age_range'])}"
    assert isinstance(persona["core_needs"], list), "core_needs 应为 list"
    assert isinstance(persona["typical_queries"], list), "typical_queries 应为 list"
    assert len(persona["typical_queries"]) >= 3, f"典型问句应 ≥3 条，实际: {len(persona['typical_queries'])}"


# ── T-A0-05：compliance_checklist() 返回非空 List[str] ──
def test_compliance_checklist():
    """合规清单：≥3 条，每条含 id/severity/description/enforcement。"""
    from app.agents.industry.registry import get_industry_pack

    pack = get_industry_pack("beauty_local")
    items = pack.compliance_checklist()
    assert isinstance(items, list), f"compliance_checklist 应返回 list，实际: {type(items)}"
    assert len(items) >= 3, f"合规清单应 ≥3 条，实际: {len(items)}"

    required_keys = {"id", "severity", "description", "enforcement"}
    for item in items:
        assert isinstance(item, dict), f"合规项应为 dict，实际: {type(item)}"
        missing = required_keys - set(item.keys())
        assert not missing, f"合规项缺字段 {missing}: {item}"


# ── T-A0-06：templates() 聚合方法返回六维 dict ──
def test_templates_aggregate():
    """templates() 返回 6 个 key 的 dict。"""
    from app.agents.industry.registry import get_industry_pack

    pack = get_industry_pack("beauty_local")
    t = pack.templates()
    assert isinstance(t, dict), f"templates() 应返回 dict，实际: {type(t)}"

    expected_keys = {
        "forbidden_words",
        "channel_weights",
        "default_persona",
        "fact_templates",
        "scenario_templates",
        "compliance_checklist",
    }
    actual_keys = set(t.keys())
    missing = expected_keys - actual_keys
    extra = actual_keys - expected_keys
    assert not missing, f"templates() 缺 key: {missing}"
    assert not extra, f"templates() 多余 key: {extra}"

    # 每个 key 的值非空
    for key in expected_keys:
        v = t[key]
        if isinstance(v, list):
            assert len(v) > 0, f"templates()['{key}'] 为空列表"
        elif isinstance(v, dict):
            assert len(v) > 0, f"templates()['{key}'] 为空 dict"
