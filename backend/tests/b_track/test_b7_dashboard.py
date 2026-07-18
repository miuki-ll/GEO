"""B7: dashboard kpi (T0/T1 Δ) + funnel four keys."""
from __future__ import annotations

from app.monitor_delta import compute_delta
from app.schemas.dashboard import DashboardData, DashboardFunnel, DashboardKpi


def test_tb7_dashboard_schema_has_handbook_keys():
    d = DashboardData(
        period="week",
        kpi=DashboardKpi(
            mention_rate_t0=0.05,
            mention_rate_t1=0.22,
            delta_mention=0.17,
            hallucination_rate=0.0,
        ),
        funnel=DashboardFunnel(
            exposure={"ok": True},
            trust={"ok": True},
            leads={"form_submits": 3},
            conversion={"manual_cost": None, "manual_revenue": None},
        ),
        geo_efficiency=0.42,
        waiting_for_a7=False,
    )
    payload = d.model_dump()
    assert set(payload["kpi"].keys()) >= {
        "mention_rate_t0",
        "mention_rate_t1",
        "delta_mention",
        "hallucination_rate",
    }
    assert set(payload["funnel"].keys()) == {"exposure", "trust", "leads", "conversion"}
    assert "geo_efficiency" in payload


def test_tb7_delta_matches_monitor_aggregate():
    t0 = [{"mentioned": False}, {"mentioned": True}]
    t1 = [{"mentioned": True}, {"mentioned": True}]
    d = compute_delta(t0, t1)
    kpi = DashboardKpi(
        mention_rate_t0=d["mention_rate_t0"],
        mention_rate_t1=d["mention_rate_t1"],
        delta_mention=d["delta_mention"],
    )
    assert kpi.mention_rate_t0 == 0.5
    assert kpi.mention_rate_t1 == 1.0
    assert kpi.delta_mention == 0.5


def test_tb7_waiting_for_a7_flag_shape():
    d = DashboardData(waiting_for_a7=True, todo="WAIT_FOR: A7")
    assert d.todo == "WAIT_FOR: A7"
    assert d.funnel.conversion["manual_cost"] is None
