"""B0: official A handoff four files (T-B0-03, T-B0-04)."""
from __future__ import annotations

import json
from pathlib import Path

from app.channel_weights import load_handoff_mock

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "handoff_a_to_b"
OFFICIAL = (
    FIXTURE_DIR / "enterprise.json",
    FIXTURE_DIR / "diagnosis.json",
    FIXTURE_DIR / "keywords.json",
    FIXTURE_DIR / "kb_facts.json",
)
README = FIXTURE_DIR / "README.md"

REQUIRED_TOP = {"enterprise", "diagnosis", "keywords", "kb_facts"}
REQUIRED_ENTERPRISE = {"id", "industry_pack", "target_engines"}
REQUIRED_DIAGNOSIS = {"source_map", "competitor_analysis", "probe_prompts", "brand_mention_rate"}


def test_tb0_03_official_four_files_section4_keys():
    assert all(p.is_file() for p in OFFICIAL), f"missing official handoff under {FIXTURE_DIR}"
    data = load_handoff_mock()
    assert REQUIRED_TOP.issubset(data.keys())
    assert REQUIRED_ENTERPRISE.issubset(data["enterprise"].keys())
    assert REQUIRED_DIAGNOSIS.issubset(data["diagnosis"].keys())
    assert "rankings" in data["diagnosis"]["source_map"]
    assert isinstance(data["keywords"], list) and len(data["keywords"]) >= 1
    assert isinstance(data["kb_facts"], list) and all("id" in f for f in data["kb_facts"])


def test_tb0_04_official_fixture_readme_marks_delivered():
    assert README.is_file()
    text = README.read_text(encoding="utf-8")
    assert "enterprise.json" in text
    assert "WAIT_FOR: A-fixture" not in text or "DELIVERED" in text or "已交付" in text
