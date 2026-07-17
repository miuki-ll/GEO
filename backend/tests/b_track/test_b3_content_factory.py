"""B3: content factory fixed chain + rag_slices (MOCK / T-B3)."""
from app.content_factory import (
    SEVEN_SEGMENT_KEYS,
    build_rag_slices,
    build_seven_segments,
    draft_api_view,
    kb_fetch,
    load_fixture_kb_facts,
    render_seven_body,
    run_fixed_chain,
)


def test_tb3_fixture_kb_facts_nonempty():
    facts = load_fixture_kb_facts()
    assert len(facts) >= 1
    assert all("id" in f and "content" in f for f in facts)


def test_tb3_kb_fetch_uses_fixture_ids():
    facts = kb_fetch(fact_ids=[1, 5, 8])
    ids = {int(f["id"]) for f in facts}
    assert ids == {1, 5, 8}


def test_tb3_seven_segments_complete():
    facts = kb_fetch()
    segs = build_seven_segments("敏感肌能不能做皮肤管理？", facts)
    assert list(segs.keys()) == list(SEVEN_SEGMENT_KEYS)
    body = render_seven_body(segs)
    for key in SEVEN_SEGMENT_KEYS:
        assert f"### {key}" in body


def test_tb3_rag_slices_shape():
    produced = run_fixed_chain(user_query="静安寺附近皮肤管理推荐", channel="hosted", skill="faq")
    assert produced["fact_refs"]
    assert isinstance(produced["rag_slices"], list) and len(produced["rag_slices"]) >= 1
    for sl in produced["rag_slices"]:
        assert {"title", "summary", "keywords", "body", "chars"} <= set(sl.keys())
        assert isinstance(sl["chars"], int) and sl["chars"] > 0
        assert sl["chars"] == len(sl["body"])


def test_tb3_rag_slice_char_bounds_helper():
    long_body = "### 结论前置\n" + ("敏感肌护理说明。" * 40)
    slices = build_rag_slices(long_body, keywords=["敏感肌"], min_chars=50, max_chars=200)
    assert slices
    assert all(s["chars"] <= 200 for s in slices)


def test_tb3_draft_api_view_shape():
    class _A:
        id = 1
        scenario_id = 9
        channel = "hosted"
        skill = "faq"
        title = "t"
        content = "body text"
        fact_refs = [1, 5]
        status = "ready"
        human_review_status = "pending"
        fact_verify_pass = True
        compliance_pass = True
        metadata_ = {
            "rag_slices": [
                {
                    "title": "x",
                    "summary": "y",
                    "keywords": ["a"],
                    "body": "z" * 10,
                    "chars": 10,
                }
            ],
            "machine_review": {
                "fact_verify": True,
                "forbidden_words": True,
                "cross_validation": True,
                "entity_consistency": True,
                "rag_readability": True,
            },
        }

    view = draft_api_view(_A())
    assert view["body"] == "body text"
    assert view["fact_refs"] == [1, 5]
    assert view["rag_slices"][0]["chars"] == 10
    assert view["machine_review"]["forbidden_words"] is True
    assert "TODO" not in str(view)  # shape only; WAIT_FOR lives in factory module
