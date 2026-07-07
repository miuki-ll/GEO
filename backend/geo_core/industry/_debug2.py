import os, sys, warnings, traceback
warnings.filterwarnings("ignore")

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(TEST_DIR, "..", "..")
sys.path.insert(0, BACKEND_DIR)
SQLITE_PATH = os.path.join(BACKEND_DIR, "_debug.sqlite3")
try: os.remove(SQLITE_PATH)
except Exception: pass
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = f"sqlite:///{SQLITE_PATH}"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["SECRET_KEY"] = "debug-secret"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "720"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from geo_core.main import create_app
from geo_core.core.db import Base, get_db
from geo_core.industry.seed import seed_beauty_enterprise

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

log_file = os.path.join(BACKEND_DIR, "_debug_report.txt")
with open(log_file, "w", encoding="utf-8") as out:
    def w(*a, **k):
        print(*a, **k, file=out, flush=True)

    with TestingSessionLocal() as db:
        seed = seed_beauty_enterprise(db, "debug美容店", "d@d.com", "Admin@12345")
        token = seed["token"].access_token

    auth = {"Authorization": f"Bearer {token}"}

    # Direct test of FactService
    with TestingSessionLocal() as db:
        from geo_core.services.kb_service import FactService
        from geo_core.schemas.kb import KBFactListParams, KBFactResponse
        try:
            items, total = FactService.list(db, 1, KBFactListParams(page=1, page_size=5))
            w("FactService.list ok:", "total=", total, "len(items)=", len(items))
            for it in items[:1]:
                loaded = FactService._post_load(it)
                w("_post_load result: id=", loaded.id, "tags=", type(loaded.tags).__name__, loaded.tags)
                val = KBFactResponse.model_validate(loaded)
                w("KBFactResponse.model_validate OK, id=", val.id, "tags=", val.tags)
        except Exception:
            w("FACT ERROR:\n", traceback.format_exc())

    w("=" * 40)
    w("TESTING /kb/facts endpoint")
    resp = client.get("/api/v1/kb/facts", headers=auth, params={"page": 1, "page_size": 5})
    w("status=", resp.status_code)
    w("content[:3000]=")
    w(resp.text[:3000])

    w("=" * 40)
    w("TESTING /strategy-pack/draft")
    resp = client.get("/api/v1/strategy-pack/draft", headers=auth)
    w("status=", resp.status_code)
    w("content[:3000]=")
    w(resp.text[:3000])

print("Report written to:", log_file)
