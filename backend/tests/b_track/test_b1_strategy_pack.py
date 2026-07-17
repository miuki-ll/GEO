"""B1 MOCK: mixed weight + five-zone draft payload (T-B1-01..04)."""
from app.channel_weights import compute_mixed_weight, build_five_zone_payload, load_handoff_mock


def test_tb1_02_mixed_weight_formula():
    assert compute_mixed_weight(0.4, 0.1) == 0.28


def test_tb1_01_03_04_five_zone_shape():
    # TODO(WAIT_FOR: A7+A8) replace mock handoff with live diagnosis/keywords
    data = build_five_zone_payload(load_handoff_mock())
    assert "persona" in data and "competitors" in data and "scenarios" in data
    assert "channels" in data and "keywords" in data
    cands = data["scenarios"]["candidates"]
    assert isinstance(cands, list)
    assert data["scenarios"]["max"] <= 5
    for c in cands:
        assert {"id", "user_query", "channel", "skill"}.issubset(c.keys())
    for ch in data["channels"]:
        assert {"model_weight", "probe_weight", "mixed_weight"}.issubset(ch.keys())
        assert abs(ch["mixed_weight"] - compute_mixed_weight(ch["model_weight"], ch["probe_weight"])) < 1e-6
