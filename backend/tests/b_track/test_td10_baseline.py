"""TD-10: baseline 字段可读写（B6 前置）。"""
from __future__ import annotations

from datetime import datetime

from app.models import MonitorResult


def test_td10_monitor_result_baseline_default_false(two_tenants):
    db = two_tenants["db"]
    e1 = two_tenants["e1"]
    row = MonitorResult(
        enterprise_id=e1.id,
        pool_type="core",
        engine="doubao",
        query="静安寺皮肤管理推荐",
        mentioned=False,
        run_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    assert row.baseline is False


def test_td10_monitor_result_baseline_t0(two_tenants):
    db = two_tenants["db"]
    e1 = two_tenants["e1"]
    t0 = MonitorResult(
        enterprise_id=e1.id,
        pool_type="core",
        engine="doubao",
        query="静安寺皮肤管理推荐",
        mentioned=True,
        baseline=True,
        run_at=datetime.utcnow(),
    )
    t1 = MonitorResult(
        enterprise_id=e1.id,
        pool_type="core",
        engine="doubao",
        query="静安寺皮肤管理推荐",
        mentioned=True,
        baseline=False,
        run_at=datetime.utcnow(),
    )
    db.add_all([t0, t1])
    db.commit()
    n_t0 = (
        db.query(MonitorResult)
        .filter(MonitorResult.enterprise_id == e1.id, MonitorResult.baseline.is_(True))
        .count()
    )
    n_t1 = (
        db.query(MonitorResult)
        .filter(MonitorResult.enterprise_id == e1.id, MonitorResult.baseline.is_(False))
        .count()
    )
    assert n_t0 == 1
    assert n_t1 == 1
