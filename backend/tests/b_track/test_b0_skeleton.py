"""B0: handoff mock schema + WAIT_FOR marker (T-B0-03, T-B0-04)."""
from __future__ import annotations

import json
from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "handoff_a_to_b"
BUNDLE = FIXTURE_DIR / "enterprise_bundle.json"
README = FIXTURE_DIR / "README.md"

REQUIRED_TOP = {"enterprise", "diagnosis", "keywords", "kb_facts"}
REQUIRED_ENTERPRISE = {"id", "industry_pack", "target_engines"}
REQUIRED_DIAGNOSIS = {"source_map", "competitor_analysis", "probe_prompts", "brand_mention_rate"}


def test_tb0_03_handoff_bundle_has_section4_keys():
    assert BUNDLE.is_file(), f"missing mock bundle: {BUNDLE}"
    data = json.loads(BUNDLE.read_text(encoding="utf-8"))
    assert REQUIRED_TOP.issubset(data.keys())
    assert REQUIRED_ENTERPRISE.issubset(data["enterprise"].keys())
    assert REQUIRED_DIAGNOSIS.issubset(data["diagnosis"].keys())
    assert "rankings" in data["diagnosis"]["source_map"]
    assert isinstance(data["keywords"], list) and len(data["keywords"]) >= 1
    assert isinstance(data["kb_facts"], list) and all("id" in f for f in data["kb_facts"])


def test_tb0_04_wait_for_a_fixture_marker_present():
    assert README.is_file()
    text = README.read_text(encoding="utf-8")
    assert "TODO(WAIT_FOR: A-fixture)" in text
