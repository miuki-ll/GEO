"""B2: confirm 落库 + 触发生成 + 负例 + 租户隔离（T-B2-01～05）。"""
from __future__ import annotations

import pytest

from app.models import ContentAsset, Scenario, StrategyPack
from app.service.strategy_service import StrategyPackService


def test_tb2_01_02_03_confirm_persists_and_triggers_content(two_tenants):
    db = two_tenants["db"]
    e1, u1 = two_tenants["e1"], two_tenants["u1"]

    pack = StrategyPackService.ensure_draft_default(db, e1.id, u1.id)
    assert pack.status == "draft"

    confirmed, extra = StrategyPackService.confirm(
        db,
        e1.id,
        u1.id,
        pack.id,
        selected_scenarios=["c1", "c2"],
    )
    assert extra["strategy_pack_id"] == confirmed.id
    assert extra["status"] == "confirmed"
    assert "/content/drafts" in extra["next_route"]
    assert confirmed.status == "confirmed"
    assert (confirmed.metadata_ or {}).get("content_job") == "triggered"
    assert (confirmed.metadata_ or {}).get("selected_scenarios") == ["c1", "c2"]

    scenarios = (
        db.query(Scenario).filter(Scenario.enterprise_id == e1.id).all()
    )
    assert len(scenarios) >= 2
    queries = {s.user_query for s in scenarios}
    assert "敏感肌能不能做皮肤管理" in queries

    drafts = (
        db.query(ContentAsset).filter(ContentAsset.enterprise_id == e1.id).all()
    )
    assert len(drafts) >= 1


def test_tb2_04_reject_empty_or_more_than_five(two_tenants):
    db = two_tenants["db"]
    e1, u1 = two_tenants["e1"], two_tenants["u1"]
    pack = StrategyPackService.ensure_draft_default(db, e1.id, u1.id)

    with pytest.raises(ValueError, match="至少"):
        StrategyPackService.confirm(db, e1.id, u1.id, pack.id, selected_scenarios=[])

    with pytest.raises(ValueError, match="最多"):
        StrategyPackService.confirm(
            db,
            e1.id,
            u1.id,
            pack.id,
            selected_scenarios=["c1", "c2", "c3", "c4", "c5", "c6"],
        )

    # 负例不得把 pack 改成 confirmed
    db.refresh(pack)
    assert pack.status == "draft"


def test_tb2_05_tenant_isolation(two_tenants):
    db = two_tenants["db"]
    e1, e2 = two_tenants["e1"], two_tenants["e2"]
    u1 = two_tenants["u1"]

    pack = StrategyPackService.ensure_draft_default(db, e1.id, u1.id)
    StrategyPackService.confirm(
        db, e1.id, u1.id, pack.id, selected_scenarios=["c1"]
    )

    assert StrategyPackService.get(db, e2.id, pack.id) is None
    other_read = (
        db.query(StrategyPack)
        .filter(StrategyPack.id == pack.id, StrategyPack.enterprise_id == e2.id)
        .first()
    )
    assert other_read is None
    leaked = (
        db.query(Scenario)
        .filter(Scenario.enterprise_id == e2.id)
        .count()
    )
    assert leaked == 0
