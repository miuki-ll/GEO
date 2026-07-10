import os
import sys
import time
import warnings

warnings.filterwarnings("ignore")

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(TEST_DIR, "..", "..")
sys.path.insert(0, BACKEND_DIR)

SQLITE_PATH = os.path.join(BACKEND_DIR, "_smoke_test.sqlite3")
if os.path.exists(SQLITE_PATH):
    try:
        os.remove(SQLITE_PATH)
    except Exception:
        pass
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = f"sqlite:///{SQLITE_PATH}"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["SECRET_KEY"] = "smoke-test-secret-key-for-geo-2024"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "720"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import create_app
from app.core.db import Base, get_db
from app.agents.industry.packs.beauty_local.seed import seed_beauty_enterprise
from app.service import UserService
from app.schemas.auth import MemberInvite


engine = create_engine(f"sqlite:///{SQLITE_PATH}", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

app = create_app()


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app, raise_server_exceptions=False)

steps_passed = 0
steps_failed = 0
results = []


def mark(name: str, ok: bool, detail: str = ""):
    global steps_passed, steps_failed, results
    if ok:
        steps_passed += 1
        results.append(("PASS", name, str(detail)[:120]))
    else:
        steps_failed += 1
        results.append(("FAIL", name, str(detail)[:200]))
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {name}{'  :: ' + str(detail)[:120] if detail else ''}")


viewer_user_id = None

print("\n" + "=" * 60)
print("STEP 1: Seed beauty enterprise (register + 20 Facts + 5 Scenarios)")
print("=" * 60)
with TestingSessionLocal() as db:
    seed = seed_beauty_enterprise(
        db,
        enterprise_name="倾城美业 · XX 路皮肤管理中心",
        user_email="owner@smoke.com",
        user_password="Admin@12345",
    )
    mark("seed_beauty_enterprise", True,
         f"facts={len(seed['facts'])} scenarios={len(seed['scenarios'])} strategies={bool(seed['strategy_pack'])}")
    token = seed["token"].access_token
    owner = seed["owner"]
    viewer = UserService.invite_member(db, seed["enterprise"].id, owner,
                                       MemberInvite(email="viewer@smoke.com", role="viewer",
                                                    full_name="访客小王", send_email=False))
    viewer_user_id = viewer.id
    viewer_token = UserService.issue_token(viewer).access_token

auth = {"Authorization": f"Bearer {token}"}
viewer_auth = {"Authorization": f"Bearer {viewer_token}"}

resp = client.get("/api/v1/auth/me", headers=auth)
mark("GET /auth/me", resp.status_code == 200, f"status={resp.status_code}")
if resp.status_code == 200:
    data = resp.json().get("data", resp.json())
    mark("owner.role == owner", data.get("role") == "owner", f"role={data.get('role')}")

mark("viewer role created", bool(viewer_user_id), f"viewer_id={viewer_user_id}")

# Step 2: KB
print("\n" + "=" * 60)
print("STEP 2: 知识库 + CRUD")
print("=" * 60)
resp = client.get("/api/v1/user/kb/summary", headers=auth)
mark("GET /kb/summary", resp.status_code == 200, resp.text[:150])
new_fact = {
    "title": "新：抗初老紧致系列",
    "content": "抗初老紧致系列主成分：麦角硫因 + 芋螺肽 + 棕榈酰五肽-4，不含香精酒精。",
    "source_type": "official",
    "source_ref": "https://store.example.com/products/anti-aging",
    "category": "product",
    "tags": ["抗衰", "新品", "成分"],
}
resp = client.post("/api/v1/user/kb/facts", headers=auth, json=new_fact)
mark("POST /kb/facts create", resp.status_code in (200, 201), f"status={resp.status_code}")
resp = client.get("/api/v1/user/kb/facts", headers=auth, params={"page": 1, "page_size": 5})
try:
    j = resp.json()
except Exception:
    j = {}
    print(f"  [DIAG] /kb/facts status={resp.status_code} text[:300]={resp.text[:300]!r}")
mark("GET /kb/facts 总事实数≥20", resp.status_code == 200 and j.get("total", 0) >= 20, f"total_facts={j.get('total', 0)}")

# Step 3: Diagnosis
print("\n" + "=" * 60)
print("STEP 3: 诊断链（痛点/画像/竞品）")
print("=" * 60)
resp = client.get("/api/v1/user/diagnosis/pain", headers=auth)
mark("GET /diagnosis/pain", resp.status_code == 200, f"n={len(resp.json().get('data', []))}")
resp = client.get("/api/v1/user/diagnosis/persona", headers=auth)
mark("GET /diagnosis/persona", resp.status_code == 200, f"age_range={resp.json().get('age_range')}")
resp = client.get("/api/v1/user/diagnosis/competitor", headers=auth)
mark("GET /diagnosis/competitor", resp.status_code == 200, f"n={len(resp.json().get('data', []))}")

# Step 4: Strategy Pack Confirm (Gate 2)
print("\n" + "=" * 60)
print("STEP 4: 方案包闸门 2 确认")
print("=" * 60)
resp = client.get("/api/v1/user/strategy-pack/draft", headers=auth)
mark("GET /strategy-pack/draft", resp.status_code == 200,
     f"status={resp.json().get('status')} version={resp.json().get('version')}")
resp = client.post("/api/v1/user/strategy-pack/confirm", headers=auth)
mark("POST /strategy-pack/confirm", resp.status_code == 200,
     f"status={resp.json().get('status')} confirmed_at={bool(resp.json().get('confirmed_at'))}")

# Step 5: Scenario + Drafts + Machine Review
print("\n" + "=" * 60)
print("STEP 5: Scenario -> Drafts 生成 -> fact_verify + compliance 机审")
print("=" * 60)
resp = client.get("/api/v1/user/content/scenarios", headers=auth)
mark("GET /content/scenarios", resp.status_code == 200, "")
scenarios = resp.json().get("data", {}).get("items", [])
scenario_ids = [s["id"] for s in scenarios if s.get("id")]
mark("Seed scenarios > 0", len(scenario_ids) > 0, f"n={len(scenario_ids)}")

draft_ids = []
if scenario_ids:
    sid = scenario_ids[0]
    resp = client.post(f"/api/v1/user/content/scenarios/{sid}/generate-drafts", headers=auth)
    status_ok = resp.status_code in (200, 201)
    resp_detail = ""
    try:
        if status_ok:
            items = resp.json().get("data", {}).get("items", [])
        else:
            items = []
            resp_detail = f" status={resp.status_code} text={resp.text[:300]!r}"
    except Exception as e:
        items = []
        resp_detail = f" status={resp.status_code} err={e} text[:300]={resp.text[:300]!r}"
    mark("POST /scenarios/{sid}/generate-drafts", status_ok,
         f"drafts_created={len(items)}{resp_detail}")
    draft_ids = [d["id"] for d in items]

for did in draft_ids[:3]:
    resp = client.post(f"/api/v1/user/content/drafts/{did}/machine-review", headers=auth)
    ok = resp.status_code == 200
    detail = ""
    if ok:
        detail = f"fact_pass={resp.json().get('fact_verify_pass')} comp_pass={resp.json().get('compliance_pass')}"
    else:
        try:
            eb = resp.json()
            detail = f"HTTP{resp.status_code} err={eb.get('detail') or eb.get('message') or str(eb)[:80]}"
        except Exception:
            detail = f"HTTP{resp.status_code} text={resp.text[:80]}"
    mark(f"draft#{did} machine_review", ok, detail)

# Step 6: Bulk Approve (Gate 3) + Publish (AUTO mode)
print("\n" + "=" * 60)
print("STEP 6: 批量审批 + 发布 AUTO")
print("=" * 60)
resp = client.get("/api/v1/user/content/drafts", headers=auth, params={"page_size": 100})
all_drafts = resp.json().get("data", {}).get("items", [])
approved_ids = []
if draft_ids:
    bulk_ids = draft_ids[:3]
    resp = client.post("/api/v1/user/content/drafts/bulk-approve", headers=auth, json={"ids": bulk_ids, "note": "smoke bulk"})
    ok = resp.status_code == 200
    mark("POST /drafts/bulk-approve 闸门3", ok,
         f"approved={resp.json().get('data', {}).get('approved_ids', []) if ok else 'ERR'}")
    if ok:
        approved_ids = resp.json().get("data", {}).get("approved_ids") or []

published_task = None
if approved_ids:
    resp = client.post("/api/v1/user/publish", headers=auth, json={
        "draft_id": approved_ids[0], "channel": "hosted", "mode": "auto"
    })
    mark("POST /publish create task (AUTO)", resp.status_code in (200, 201), f"task_id={resp.json().get('id')}")
    if resp.status_code in (200, 201):
        tid = resp.json()["id"]
        resp = client.post(f"/api/v1/user/publish/{tid}/auto", headers=auth)
        status_ok = resp.status_code == 200
        status_val = None
        pub_detail = ""
        if status_ok:
            try:
                status_val = resp.json().get("status")
                pub_detail = f"status={status_val} url={resp.json().get('published_url', '')[:60]}"
            except Exception as e:
                pub_detail = f" resp parse err={e} text[:100]={resp.text[:100]}"
        else:
            try:
                eb = resp.json()
                pub_detail = f"HTTP{resp.status_code} err={eb.get('detail') or eb.get('message') or str(eb)[:100]}"
            except Exception:
                pub_detail = f"HTTP{resp.status_code} text={resp.text[:100]}"
        ok = status_ok and status_val == "published"
        mark("POST /publish/{tid}/auto 执行发布", ok, pub_detail)

# Step 7: Monitor Core + Probe
print("\n" + "=" * 60)
print("STEP 7: 监测 Core + Probe + 趋势")
print("=" * 60)
resp = client.post("/api/v1/user/monitor/trigger", headers=auth, json={"pool": "core", "scenario_ids": scenario_ids[:3]})
mark("POST /monitor/trigger core", resp.status_code == 200, f"batch={resp.json().get('data', {}).get('batch_no','')[:24]} created={resp.json().get('data', {}).get('created', 0)}")
resp = client.post("/api/v1/user/monitor/trigger", headers=auth, json={"pool": "probe", "scenario_ids": []})
mark("POST /monitor/trigger probe", resp.status_code == 200, f"created={resp.json().get('data', {}).get('created', 0)}")

resp = client.get("/api/v1/user/monitor/core", headers=auth, params={"page_size": 10})
mark("GET /monitor/core list", resp.status_code == 200,
     f"total_samples={resp.json().get('data', {}).get('total', 0)}")
resp = client.get("/api/v1/user/monitor/trend", headers=auth, params={"pool": "core", "days": 7})
mark("GET /monitor/trend 7d", resp.status_code == 200, f"points={len(resp.json().get('data', []))}")

# Step 8: Dashboard + Iteration Closed Loop (G2)
print("\n" + "=" * 60)
print("STEP 8: 效果舱 Dashboard + G2 临界触发迭代闭环")
print("=" * 60)
resp = client.get("/api/v1/user/outcomes/dashboard", headers=auth, params={"period": "week"})
ok = resp.status_code == 200
raw = resp.json() if ok else {}
d = raw.get("data", raw) if isinstance(raw, dict) else {}
mark("GET /outcomes/dashboard", ok, "")
if ok:
    mark("Dashboard.has KPI", all(k in d for k in ("kpi", "by_channel", "by_engine", "trend", "alerts")),
         f"keys={list(d.keys())}")
    kpi = d.get("kpi", {})
    print(f"    KPI summary: scenarios={kpi.get('total_scenarios')} published={kpi.get('total_drafts_published')} "
          f"mention_rate={kpi.get('avg_mention_rate')} trust={kpi.get('avg_trust_score')} pending_review={kpi.get('pending_review')}")
    if d.get("alerts"):
        for a in d["alerts"][:5]:
            print(f"    ALERT [{a.get('level')}] {a.get('msg')}")
resp = client.get("/api/v1/user/outcomes/ai-kpi", headers=auth)
mark("GET /outcomes/ai-kpi", resp.status_code == 200, "")
resp = client.get("/api/v1/user/outcomes/traffic", headers=auth)
mark("GET /outcomes/traffic", resp.status_code == 200,
     f"channels={len(resp.json().get('data', {}).get('by_channel', []))} engines={len(resp.json().get('data', {}).get('by_engine', []))}")

resp = client.post("/api/v1/user/outcomes/iterations/trigger", headers=auth,
                    json={"reason": "冒烟测试：提及率低阈值触发迭代"})
ok = resp.status_code in (200, 201)
raw = resp.json() if ok else {}
task_wrap = raw.get("data", raw) if isinstance(raw, dict) else {}
t_id = task_wrap.get("task_id", task_wrap.get("id"))
mark("POST iterations/trigger G2 迭代闭环 Agent", ok and t_id is not None,
     f"task_id={t_id if ok else 'ERR'} type={task_wrap.get('task_type') if ok else 'ERR'} status={task_wrap.get('status') if ok else 'ERR'}")
if ok and t_id:
    for _ in range(3):
        time.sleep(0.3)
        resp = client.get(f"/api/v1/agent/{t_id}", headers=auth)
        if resp.status_code == 200 and resp.json().get("progress_pct", 0) > 10:
            break
    pct = resp.json().get("progress_pct", -1) if resp.status_code == 200 else -1
    mark("GET Agent task status 迭代闭环", resp.status_code == 200,
         f"status={resp.json().get('status') if resp.status_code == 200 else 'ERR'} pct={pct}")

# Step 9: RBAC viewer role rejection check
print("\n" + "=" * 60)
print("STEP 9: RBAC viewer 权限拦截校验 + LLM Gateway")
print("=" * 60)
resp = client.post("/api/v1/user/content/scenarios", headers=viewer_auth, json={
    "title": "viewer try create scenario",
    "user_query": "unauthorized test",
    "channel": "hosted",
    "skill": "faq",
    "priority": 5,
})
mark("viewer 创建 scenario → 403 拒绝", resp.status_code == 403, f"status={resp.status_code} (expect 403)")

resp = client.get("/api/v1/llm/engines", headers=auth)
mark("GET /llm/engines", resp.status_code == 200, f"engines={len(resp.json().get('data', []))}")

# Final: Summarize
print("\n" + "=" * 60)
print(f"SMOKE TEST END: PASS={steps_passed}  FAIL={steps_failed}  TOTAL={steps_passed + steps_failed}")
print("=" * 60)
for s, n, d in results:
    print(f"  [{s:4s}] {n}{'  —  ' + d if d else ''}")

try:
    engine.dispose()
except Exception:
    pass
try:
    if os.path.exists(SQLITE_PATH):
        os.remove(SQLITE_PATH)
except Exception:
    pass

sys.exit(0 if steps_failed == 0 else 1)
