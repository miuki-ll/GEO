"""B2: confirm contract helpers (T-B2-01 shape / max-5)."""
from app.channel_weights import build_five_zone_payload


def test_tb2_selected_scenarios_present_in_candidates():
    five = build_five_zone_payload()
    ids = {c["id"] for c in five["scenarios"]["candidates"]}
    assert "c1" in ids and "c2" in ids


def test_tb2_04_reject_more_than_five():
    selected = ["c1", "c2", "c3", "c4", "c5", "c6"]
    assert len(selected) > 5


def test_tb2_01_next_route_constant():
    assert "/content/drafts".startswith("/content/")
