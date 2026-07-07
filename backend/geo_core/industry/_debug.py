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
from geo_core.services import UserService
from geo_core.schemas.auth import MemberInvite

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

with TestingSessionLocal() as db:
    seed = seed_beauty_enterprise(db, "debug美容店", "d@d.com", "Admin@12345")
    token = seed["token"].access_token

auth = {"Authorization": f"Bearer {token}"}
print("======== TEST /kb/facts ========")
try:
    with TestingSessionLocal() as db:
        from geo_core.services.kb_service import FactService
        from geo_core.schemas.kb import KBFactListParams
        items, total = FactService.list(db, 1, KBFactListParams(page=1, page_size=5))
        print(f"service ok: total={total} items[0]={items[0].__dict__ if items else None}")
        try:
            loaded = FactService._post_load(items[0])
            print(f"_post_load ok: loaded.tags={loaded.tags!r}")
            from geo_core.schemas.kb import KBFactResponse
            val = KBFactResponse.model_validate(loaded)
            print(f"KBFactResponse.model_validate ok: {val.model_dump()!r}")
        except Exception as ee:
            import traceback
            traceback.print_exc()
except Exception:
    import traceback
    traceback.print_exc()
print("======== END /kb/facts diagnose ========")
resp = client.get("/api/v1/kb/facts", headers=auth, params={"page": 1, "page_size": 5})
print("status=", resp.status_code)
print(resp.text[:1500])
print("======== TEST /strategy-pack/draft ========")
resp = client.get("/api/v1/strategy-pack/draft", headers=auth)
print("status=", resp.status_code)
print(resp.text[:5000])
