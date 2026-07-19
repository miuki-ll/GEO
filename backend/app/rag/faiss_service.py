"""Faiss per-tenant 向量库 — add/search/delete/rebuild + 磁盘持久化

- 每个租户每种类型（kb_facts / kb_faqs）一个独立 Faiss 索引文件
- 使用 IndexIDMap(IndexFlatIP(384))，支持按 ID 增删
- 索引持久化到 backend/faiss_data/{enterprise_id}/ 目录
"""
import os
import threading
from typing import Dict, List, Optional, Tuple

import faiss
import numpy as np

from app.core.config import settings
from app.core.embedding import get_embedding_function
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# 索引文件存放根目录
FAISS_ROOT = os.path.join(settings.PROJECT_ROOT, "faiss_data")

# 全局锁：每个索引一把锁，防止并发读写
_LOCKS: Dict[str, threading.Lock] = {}
_LOCKS_LOCK = threading.Lock()  # 保护 _LOCKS 字典本身


def _get_lock(key: str) -> threading.Lock:
    """获取或创建指定 key 的锁"""
    with _LOCKS_LOCK:
        if key not in _LOCKS:
            _LOCKS[key] = threading.Lock()
        return _LOCKS[key]


class FaissService:
    """Faiss 向量索引服务 — per-tenant + per-type 隔离"""

    # 支持的索引类型
    INDEX_TYPES = ("kb_facts", "kb_faqs")
    # text2vec-base-chinese 的向量维度（原 step 写 bge=384；本机改用 text2vec=768）
    VECTOR_DIM = 768

    _embedding_model = None  # 延迟加载

    @classmethod
    def _get_embedding(cls):
        """延迟加载 embedding 模型（首次调用时加载，之后复用）"""
        if cls._embedding_model is None:
            cls._embedding_model = get_embedding_function()
        return cls._embedding_model

    # ── 路径工具 ──

    @classmethod
    def _index_dir(cls, enterprise_id: int) -> str:
        """获取租户的索引目录"""
        d = os.path.join(FAISS_ROOT, str(enterprise_id))
        os.makedirs(d, exist_ok=True)
        return d

    @classmethod
    def _index_path(cls, enterprise_id: int, index_type: str) -> str:
        """获取索引文件完整路径"""
        return os.path.join(cls._index_dir(enterprise_id), f"{index_type}.index")

    # ── 索引加载/保存 ──

    @classmethod
    def _load_index(cls, enterprise_id: int, index_type: str) -> faiss.IndexIDMap:
        """加载索引，不存在则创建空索引"""
        path = cls._index_path(enterprise_id, index_type)
        if os.path.exists(path):
            logger.info("[faiss] load index %s eid=%s", index_type, enterprise_id)
            return faiss.read_index(path)
        # 创建空索引：内积相似度（向量已归一化时等价余弦相似度）
        base = faiss.IndexFlatIP(cls.VECTOR_DIM)
        idx = faiss.IndexIDMap(base)
        logger.info("[faiss] create empty index %s eid=%s", index_type, enterprise_id)
        return idx

    @classmethod
    def _save_index(cls, enterprise_id: int, index_type: str, index: faiss.IndexIDMap):
        """保存索引到磁盘"""
        path = cls._index_path(enterprise_id, index_type)
        faiss.write_index(index, path)
        logger.info("[faiss] saved index %s eid=%s ntotal=%s", index_type, enterprise_id, index.ntotal)

    # ── 公开 API ──

    @classmethod
    def add(
        cls,
        enterprise_id: int,
        index_type: str,
        texts: List[str],
        ids: List[int],
    ) -> int:
        """批量添加文本到索引。

        Args:
            enterprise_id: 租户 ID
            index_type: "kb_facts" 或 "kb_faqs"
            texts: 文本列表（与 ids 一一对应）
            ids: 记录 ID 列表（数据库主键，用作 Faiss 向量 ID）

        Returns:
            添加的向量数量
        """
        if index_type not in cls.INDEX_TYPES:
            raise ValueError(f"index_type 必须是 {cls.INDEX_TYPES} 之一，实际: {index_type}")
        if not texts:
            return 0

        emb = cls._get_embedding()
        vectors = emb.embed_documents(texts)
        np_vectors = np.array(vectors, dtype=np.float32)
        np_ids = np.array(ids, dtype=np.int64)

        lock = _get_lock(f"{enterprise_id}:{index_type}")
        with lock:
            index = cls._load_index(enterprise_id, index_type)
            index.add_with_ids(np_vectors, np_ids)
            cls._save_index(enterprise_id, index_type, index)

        logger.info("[faiss] add eid=%s type=%s count=%s", enterprise_id, index_type, len(texts))
        return len(texts)

    @classmethod
    def search(
        cls,
        enterprise_id: int,
        index_type: str,
        query: str,
        top_k: int = 5,
    ) -> List[Tuple[int, float]]:
        """语义搜索 — 返回 (id, score) 列表，按相似度降序。

        Args:
            enterprise_id: 租户 ID
            index_type: "kb_facts" 或 "kb_faqs"
            query: 查询文本
            top_k: 返回条数

        Returns:
            [(id, score), ...] — score 越高越相似
        """
        if index_type not in cls.INDEX_TYPES:
            return []

        emb = cls._get_embedding()
        query_vec = emb.embed_query(query)
        np_query = np.array([query_vec], dtype=np.float32)

        lock = _get_lock(f"{enterprise_id}:{index_type}")
        with lock:
            index = cls._load_index(enterprise_id, index_type)
            if index.ntotal == 0:
                return []
            scores, idxs = index.search(np_query, min(top_k, index.ntotal))

        # 过滤无效结果（id=-1 表示未找到）
        results = []
        for i in range(len(idxs[0])):
            if idxs[0][i] != -1:
                results.append((int(idxs[0][i]), float(scores[0][i])))
        return results

    @classmethod
    def delete(
        cls,
        enterprise_id: int,
        index_type: str,
        ids: List[int],
    ) -> int:
        """从索引中删除指定 ID 的向量。

        Args:
            enterprise_id: 租户 ID
            index_type: "kb_facts" 或 "kb_faqs"
            ids: 要删除的记录 ID 列表

        Returns:
            实际删除的数量
        """
        if index_type not in cls.INDEX_TYPES or not ids:
            return 0

        np_ids = np.array(ids, dtype=np.int64)
        lock = _get_lock(f"{enterprise_id}:{index_type}")
        with lock:
            index = cls._load_index(enterprise_id, index_type)
            if index.ntotal == 0:
                return 0
            removed = index.remove_ids(np_ids)
            cls._save_index(enterprise_id, index_type, index)

        logger.info("[faiss] delete eid=%s type=%s removed=%s", enterprise_id, index_type, removed)
        return int(removed)

    @classmethod
    def rebuild(
        cls,
        enterprise_id: int,
        index_type: str,
    ) -> int:
        """全量重建索引 — 从数据库拉取全部记录，重新 embed 并建索引。

        Args:
            enterprise_id: 租户 ID
            index_type: "kb_facts" 或 "kb_faqs"

        Returns:
            重建后的向量数量
        """
        if index_type not in cls.INDEX_TYPES:
            raise ValueError(f"index_type 必须是 {cls.INDEX_TYPES} 之一，实际: {index_type}")

        from app.core.db import SessionLocal
        from app.models.kb import KBFact, KBFaq

        db = SessionLocal()
        try:
            if index_type == "kb_facts":
                rows = db.query(KBFact).filter(
                    KBFact.enterprise_id == enterprise_id,
                    KBFact.content.isnot(None),
                    KBFact.content != "",
                ).all()
                texts = [r.title + " " + r.content for r in rows]
            else:
                rows = db.query(KBFaq).filter(
                    KBFaq.enterprise_id == enterprise_id,
                    KBFaq.answer.isnot(None),
                    KBFaq.answer != "",
                ).all()
                texts = [r.question + " " + r.answer for r in rows]

            ids = [r.id for r in rows]

            if not texts:
                # 清空索引
                lock = _get_lock(f"{enterprise_id}:{index_type}")
                with lock:
                    base = faiss.IndexFlatIP(cls.VECTOR_DIM)
                    idx = faiss.IndexIDMap(base)
                    cls._save_index(enterprise_id, index_type, idx)
                logger.info("[faiss] rebuild empty %s eid=%s", index_type, enterprise_id)
                return 0

            emb = cls._get_embedding()
            vectors = emb.embed_documents(texts)
            np_vectors = np.array(vectors, dtype=np.float32)
            np_ids = np.array(ids, dtype=np.int64)

            base = faiss.IndexFlatIP(cls.VECTOR_DIM)
            idx = faiss.IndexIDMap(base)
            idx.add_with_ids(np_vectors, np_ids)

            lock = _get_lock(f"{enterprise_id}:{index_type}")
            with lock:
                cls._save_index(enterprise_id, index_type, idx)

            logger.info("[faiss] rebuild done %s eid=%s count=%s", index_type, enterprise_id, len(texts))
            return len(texts)
        finally:
            db.close()

    @classmethod
    def index_stats(cls, enterprise_id: int, index_type: str) -> dict:
        """获取索引统计信息"""
        if index_type not in cls.INDEX_TYPES:
            return {"exists": False, "ntotal": 0}
        path = cls._index_path(enterprise_id, index_type)
        if not os.path.exists(path):
            return {"exists": False, "ntotal": 0, "path": path}
        idx = cls._load_index(enterprise_id, index_type)
        return {
            "exists": True,
            "ntotal": idx.ntotal,
            "path": path,
            "dimension": cls.VECTOR_DIM,
        }
