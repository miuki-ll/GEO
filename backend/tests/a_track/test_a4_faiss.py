"""A4 Faiss 向量库测试 — add/search/delete/rebuild

用例对照 G-L3-开发者A任务手册.md §11.3：
  T-A4-01 ~ T-A4-03

适配说明（相对 step 骨架）：
  - MockEmbedding 维度跟 FaissService.VECTOR_DIM（本机 text2vec=768，非 bge 的 384）
  - 向量用字符袋生成，保证相近文本 IP>0（纯 hash 随机向量可能为负）
  - T-A4-03 monkeypatch SessionLocal → db_session（rebuild 内部用 SessionLocal，非 fixture）
"""
import os
import numpy as np
import pytest

from sqlalchemy.orm import Session


# ═══════════════════ Mock Embedding 工具 ═══════════════════

class MockEmbedding:
    """返回固定维度的确定性向量，不依赖真实模型。"""

    def __init__(self, dim: int = 768):
        self._dim = dim

    def _vec_for(self, text: str) -> np.ndarray:
        # 字符袋 → 相近文本有正内积（匹配 IndexFlatIP + 归一化）
        v = np.zeros(self._dim, dtype=np.float32)
        for ch in text:
            v[hash(ch) % self._dim] += 1.0
        n = np.linalg.norm(v)
        if n > 0:
            v = v / n
        else:
            v[0] = 1.0
        return v

    def embed_documents(self, texts: list) -> list:
        return [self._vec_for(t).tolist() for t in texts]

    def embed_query(self, text: str) -> list:
        return self.embed_documents([text])[0]


# ═══════════════════ 测试用例 ═══════════════════

TEST_EID = 9999
TEST_TYPE = "kb_facts"


@pytest.fixture(autouse=True)
def _mock_embedding(monkeypatch):
    """全局 mock：所有测试用固定向量替代真实 embedding 模型"""
    from app.rag.faiss_service import FaissService

    mock = MockEmbedding(dim=FaissService.VECTOR_DIM)
    monkeypatch.setattr("app.rag.faiss_service.FaissService._embedding_model", mock)


@pytest.fixture
def _cleanup():
    """测试结束后清理临时索引文件"""
    yield
    from app.rag.faiss_service import FaissService
    path = FaissService._index_path(TEST_EID, TEST_TYPE)
    if os.path.exists(path):
        os.remove(path)
    # 同时清理 rebuild 测试用的 eid=8888
    p2 = FaissService._index_path(8888, TEST_TYPE)
    if os.path.exists(p2):
        os.remove(p2)
    p3 = FaissService._index_path(8888, "kb_faqs")
    if os.path.exists(p3):
        os.remove(p3)


# ── T-A4-01：add + search ──

@pytest.mark.usefixtures("_cleanup")
def test_add_and_search():
    """T-A4-01：添加文本后能语义搜索到。"""
    from app.rag.faiss_service import FaissService

    # 添加
    count = FaissService.add(TEST_EID, TEST_TYPE,
                             texts=["补水保湿是皮肤管理的基础护理步骤"],
                             ids=[1])
    assert count == 1

    # 搜索
    results = FaissService.search(TEST_EID, TEST_TYPE, "补水保湿", top_k=3)
    assert len(results) == 1
    assert results[0][0] == 1  # id
    assert results[0][1] > 0   # score > 0


# ── T-A4-02：delete ──

@pytest.mark.usefixtures("_cleanup")
def test_delete():
    """T-A4-02：删除后搜不到被删的条目。"""
    from app.rag.faiss_service import FaissService

    # 添加 2 条
    FaissService.add(TEST_EID, TEST_TYPE,
                     texts=["补水护理指南", "控油护肤方法"],
                     ids=[1, 2])

    results = FaissService.search(TEST_EID, TEST_TYPE, "护肤", top_k=5)
    assert len(results) == 2

    # 删除 id=1
    FaissService.delete(TEST_EID, TEST_TYPE, [1])

    results = FaissService.search(TEST_EID, TEST_TYPE, "护肤", top_k=5)
    ids = [r[0] for r in results]
    assert 1 not in ids, "删除后 id=1 不应出现在结果中"
    assert 2 in ids, "id=2 应该还在"


# ── T-A4-03：rebuild ──

@pytest.mark.usefixtures("_cleanup")
def test_rebuild(db_session: Session, monkeypatch):
    """T-A4-03：从数据库全量重建索引。"""
    from app.rag.faiss_service import FaissService
    from app.models.kb import KBFact
    from app.models import Enterprise

    eid = 8888

    # rebuild() 内部 SessionLocal() → 指到本测试的内存库；close() 不关 fixture
    class _SessionProxy:
        def __init__(self, real):
            self._real = real

        def __getattr__(self, name):
            return getattr(self._real, name)

        def close(self):
            pass

    monkeypatch.setattr(
        "app.core.db.SessionLocal",
        lambda: _SessionProxy(db_session),
    )

    # 创建测试租户和 KB 记录
    ent = Enterprise(name="Faiss测试企业", industry_pack="beauty_local", status="active")
    db_session.add(ent)
    db_session.flush()

    f1 = KBFact(enterprise_id=eid, title="补水保湿", content="皮肤补水是基础护理第一步")
    f2 = KBFact(enterprise_id=eid, title="控油祛痘", content="油性肌肤需要温和清洁")
    db_session.add_all([f1, f2])
    db_session.commit()

    # rebuild
    count = FaissService.rebuild(eid, TEST_TYPE)
    assert count == 2

    # 搜索
    results = FaissService.search(eid, TEST_TYPE, "补水保湿护理", top_k=5)
    assert len(results) >= 1, f"rebuild 后应能搜到，实际 {results}"

    # 更新一条 → rebuild → 验证
    f1.content = "更新后的内容：激光祛斑技术介绍"
    db_session.commit()

    FaissService.rebuild(eid, TEST_TYPE)

    # 搜索新内容
    results = FaissService.search(eid, TEST_TYPE, "激光祛斑", top_k=5)
    assert len(results) >= 1, "rebuild 后应能搜到更新后的内容"

    # 清理数据库（测试结束后自动 drop_all，这里只删索引文件）
    db_session.rollback()
