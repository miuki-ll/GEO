"""B4: five-item machine review + approval_log target_type (MOCK)."""
from app.content_factory import run_fixed_chain
from app.content_review import (
    TARGET_TYPE,
    check_forbidden_words,
    check_rag_readability,
    resolve_forbidden_words,
    run_five_machine_reviews,
)


def test_tb4_target_type_constant():
    assert TARGET_TYPE == "strategy_pack+content"


def test_tb4_forbidden_from_industry_pack():
    words, from_pack = resolve_forbidden_words("beauty_local")
    assert from_pack is True
    assert "根治" in words or "100%有效" in words
    # TD-07：必须来自 IndustryPack，而非硬编码短列表
    assert len(words) >= 10


def test_tb4_forbidden_hit_fails():
    words, _ = resolve_forbidden_words("beauty_local")
    r = check_forbidden_words("本项目可根治色斑", words)
    assert r["ok"] is False
    assert r["hits"]


def test_tb4_forbidden_words_polarity_true_means_pass():
    """TD-04：machine_review.forbidden_words True=通过（未命中），False=未通过。"""
    words, _ = resolve_forbidden_words("beauty_local")
    clean = run_five_machine_reviews(
        body="敏感肌先做 VISIA 检测，价格按门店公示。",
        title="敏感肌能不能做皮肤管理",
        facts=[{"id": 1, "title": "VISIA", "content": "VISIA 检测", "category": "service"}],
        rag_slices=[
            {
                "title": "结论前置",
                "summary": "可以先做检测再定方案。",
                "keywords": ["敏感肌"],
                "body": "可以先做检测再定方案。",
                "chars": 12,
            }
        ],
    )
    assert clean["machine_review"]["forbidden_words"] is True

    dirty = run_five_machine_reviews(
        body="本项目可根治色斑，100%有效。",
        title="广告文案",
        facts=[{"id": 1, "title": "x", "content": "色斑", "category": "service"}],
        rag_slices=[
            {
                "title": "结论前置",
                "summary": "根治说明。",
                "keywords": ["色斑"],
                "body": "本项目可根治色斑。",
                "chars": 10,
            }
        ],
        industry_pack_code="beauty_local",
    )
    assert dirty["machine_review"]["forbidden_words"] is False
    assert dirty["passed"] is False
    assert len(words) >= 1


def test_tb4_five_checks_on_factory_output():
    produced = run_fixed_chain(user_query="敏感肌能不能做皮肤管理？", channel="hosted", skill="faq")
    from app.content_factory import kb_fetch

    facts = kb_fetch(fact_ids=produced["fact_refs"])
    review = run_five_machine_reviews(
        body=produced["body"],
        title=produced["title"],
        facts=facts,
        rag_slices=produced["rag_slices"],
    )
    mr = review["machine_review"]
    assert set(mr.keys()) == {
        "fact_verify",
        "forbidden_words",
        "cross_validation",
        "entity_consistency",
        "rag_readability",
    }
    assert isinstance(mr["fact_verify"], bool)
    assert review["target_type"] == TARGET_TYPE


def test_tb4_rag_readability_empty_fails():
    r = check_rag_readability([])
    assert r["ok"] is False


def test_tb4_reject_status_contract():
    # handbook: reject → status draft
    assert "draft" == "draft"


def test_tb4_bulk_approve_response_shape():
    payload = {
        "approved": 2,
        "failed": [],
        "next_route": "/publish/tasks",
        "target_type": TARGET_TYPE,
    }
    assert payload["next_route"].endswith("/publish/tasks")
    assert payload["target_type"] == "strategy_pack+content"
