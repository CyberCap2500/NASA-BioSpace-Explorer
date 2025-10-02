import os
import sqlite3
from typing import List, Dict, Any, Tuple

import numpy as np

try:
    import faiss  # type: ignore
except Exception as e:  # pragma: no cover
    faiss = None  # type: ignore


class SQLiteMetadata:
    def __init__(self, db_path: str) -> None:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._init_tables()

    def _init_tables(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT,
                abstract TEXT,
                year INTEGER,
                authors TEXT,
                url TEXT,
                organism TEXT,
                keywords TEXT
            )
            """
        )
        self.conn.commit()

    def upsert_documents(self, docs: List[Dict[str, Any]]) -> None:
        cur = self.conn.cursor()
        cur.executemany(
            """
            INSERT INTO documents(id, title, abstract, year, authors, url, organism, keywords)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                abstract=excluded.abstract,
                year=excluded.year,
                authors=excluded.authors,
                url=excluded.url,
                organism=excluded.organism,
                keywords=excluded.keywords
            """,
            [
                (
                    d.get("id"),
                    d.get("title"),
                    d.get("abstract"),
                    d.get("year"),
                    d.get("authors"),
                    d.get("url"),
                    d.get("organism"),
                    ",".join(d.get("keywords", []) or []),
                )
                for d in docs
            ],
        )
        self.conn.commit()

    def get_documents(self, ids: List[str]) -> List[Dict[str, Any]]:
        q_marks = ",".join(["?"] * len(ids))
        cur = self.conn.cursor()
        cur.execute(f"SELECT * FROM documents WHERE id IN ({q_marks})", ids)
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
        docs: List[Dict[str, Any]] = []
        for r in rows:
            doc = dict(zip(cols, r))
            if isinstance(doc.get("keywords"), str):
                doc["keywords"] = [k for k in doc["keywords"].split(",") if k]
            docs.append(doc)
        return docs

    def filter(self, organism=None, year_from=None, year_to=None, keywords=None, limit=50) -> List[Dict[str, Any]]:
        clauses = []
        params: List[Any] = []
        if organism:
            clauses.append("organism = ?")
            params.append(organism)
        if year_from is not None:
            clauses.append("year >= ?")
            params.append(year_from)
        if year_to is not None:
            clauses.append("year <= ?")
            params.append(year_to)
        if keywords:
            for kw in keywords:
                clauses.append("keywords LIKE ?")
                params.append(f"%{kw}%")
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM documents{where} ORDER BY year DESC LIMIT ?"
        params.append(limit)
        cur = self.conn.cursor()
        cur.execute(sql, params)
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
        docs = []
        for r in rows:
            doc = dict(zip(cols, r))
            if isinstance(doc.get("keywords"), str):
                doc["keywords"] = [k for k in doc["keywords"].split(",") if k]
            docs.append(doc)
        return docs


class FaissIndex:
    def __init__(self, index_path: str, dim: int) -> None:
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        self.index_path = index_path
        self.dim = dim
        self.index = None
        self._load_or_create()

    def _load_or_create(self) -> None:
        global faiss
        if faiss is None:
            raise RuntimeError("faiss-cpu is not installed")
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            self.dim = self.index.d
        else:
            self.index = faiss.IndexFlatIP(self.dim)

    def save(self) -> None:
        global faiss
        if faiss is None:
            raise RuntimeError("faiss-cpu is not installed")
        faiss.write_index(self.index, self.index_path)

    def add(self, vectors: np.ndarray) -> Tuple[int, int]:
        before = self.index.ntotal
        self.index.add(vectors.astype(np.float32))
        after = self.index.ntotal
        return before, after

    def search(self, query_vecs: np.ndarray, top_k: int) -> Tuple[np.ndarray, np.ndarray]:
        scores, idxs = self.index.search(query_vecs.astype(np.float32), top_k)
        return scores, idxs



