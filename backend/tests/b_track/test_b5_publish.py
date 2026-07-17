"""B5: SEMI export_package + AUTO mock + PublishService.run_batch（T-B5）。"""
from __future__ import annotations

from app.models import ContentAsset
from app.publish_export import (
    build_auto_mock_result,
    build_semi_export_package,
    infer_publish_mode,
    publish_task_api_view,
)
from app.schemas.publish import PublishTaskCreate
from app.service.publish_service import PublishService


def test_tb5_infer_mode():
    assert infer_publish_mode("hosted") == "auto"
    assert infer_publish_mode("xiaohongshu") == "semi"
    assert infer_publish_mode("zhihu") == "semi"
    assert infer_publish_mode("dianping") == "guided"


def test_tb5_semi_export_five_fields():
    pkg = build_semi_export_package(
        title="敏感肌补水修护全流程",
        body="### 结论\n先做 VISIA 再定方案。",
        channel="xiaohongshu",
        keywords=["敏感肌", "补水"],
    )
    assert set(pkg.keys()) >= {"title", "body", "tags", "cover_hint", "steps"}
    assert pkg["title"]
    assert pkg["body"]
    assert isinstance(pkg["tags"], list) and pkg["tags"]
    assert pkg["cover_hint"]
    assert isinstance(pkg["steps"], list) and len(pkg["steps"]) >= 3


def test_tb5_auto_mock_has_url_and_schema():
    r = build_auto_mock_result(enterprise_id=1, task_id=9)
    assert r["published_url"].startswith("https://")
    assert r["schema_snippet"]["@type"] == "LocalBusiness"
    assert r.get("todo") == "WAIT_FOR: A5"


def test_tb5_task_view_content_asset_id():
    class T:
        id = 3
        content_asset_id = 42
        channel = "xiaohongshu"
        mode = "semi"
        status = "pending"
        published_url = None
        published_id = None
        published_at = None
        retry_count = 0
        fallback_semi = False
        error_message = None
        enterprise_id = 1
        metadata_ = {
            "export_package": build_semi_export_package(
                title="t", body="b", channel="xiaohongshu"
            )
        }

    class A:
        title = "草稿标题"

    view = publish_task_api_view(T(), A())
    assert view["content_asset_id"] == 42
    assert view["draft_id"] == 42
    assert view["export_package"]["title"] == "t"
    assert view["title"] == "草稿标题"


def test_tb5_run_batch_auto_and_semi(two_tenants):
    """真实调用 PublishService.run_batch（替代假 {started:2} 断言）。"""
    db = two_tenants["db"]
    e1 = two_tenants["e1"]

    from app.models import Scenario

    sc = Scenario(
        enterprise_id=e1.id,
        title="测试场景",
        user_query="敏感肌能不能做皮肤管理",
        intent="项目咨询",
        channel="hosted",
        skill="faq",
        status="ready",
    )
    db.add(sc)
    db.flush()

    auto_asset = ContentAsset(
        enterprise_id=e1.id,
        scenario_id=sc.id,
        title="托管页 FAQ",
        content="### 结论\n可以。",
        channel="hosted",
        skill="faq",
        status="approved",
        fact_refs=[1],
        metadata_={"rag_slices": [{"title": "t", "summary": "s", "keywords": ["a"], "body": "b", "chars": 1}]},
    )
    semi_asset = ContentAsset(
        enterprise_id=e1.id,
        scenario_id=sc.id,
        title="小红书笔记",
        content="### 结论\n先做 VISIA。",
        channel="xiaohongshu",
        skill="article",
        status="approved",
        fact_refs=[1],
        metadata_={},
    )
    db.add_all([auto_asset, semi_asset])
    db.commit()
    db.refresh(auto_asset)
    db.refresh(semi_asset)

    t_auto = PublishService.create(
        db,
        e1.id,
        PublishTaskCreate(draft_id=auto_asset.id, channel="hosted", mode="auto"),
    )
    t_semi = PublishService.create(
        db,
        e1.id,
        PublishTaskCreate(draft_id=semi_asset.id, channel="xiaohongshu", mode="semi"),
    )
    assert (t_semi.metadata_ or {}).get("export_package")
    pkg = t_semi.metadata_["export_package"]
    assert set(pkg.keys()) >= {"title", "body", "tags", "cover_hint", "steps"}

    out = PublishService.run_batch(db, e1.id, [t_auto.id, t_semi.id])
    assert out["started"] == 2
    assert all(r.get("ok") for r in out["results"])

    db.refresh(t_auto)
    db.refresh(t_semi)
    assert t_auto.status == "published"
    assert t_auto.published_url and t_auto.published_url.startswith("https://")
    assert t_semi.status == "pending"  # SEMI 待人工回填
    assert (t_semi.metadata_ or {}).get("export_package", {}).get("title")


def test_tb5_run_batch_unknown_task(two_tenants):
    db = two_tenants["db"]
    e1 = two_tenants["e1"]
    out = PublishService.run_batch(db, e1.id, [99999])
    assert out["started"] == 0
    assert out["results"][0]["ok"] is False
