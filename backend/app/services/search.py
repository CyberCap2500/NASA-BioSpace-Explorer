import os
from typing import List, Optional, Dict, Any, Tuple

import numpy as np

from app.services.embeddings import EmbeddingsClient
from app.services.vector_store import FaissIndex, SQLiteMetadata

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

try:
    from transformers import pipeline  # type: ignore
except Exception:
    pipeline = None  # type: ignore


class SearchService:
    def __init__(self, index_path: str, metadata_db_path: str) -> None:
        self.index_path = index_path
        self.metadata = SQLiteMetadata(metadata_db_path)
        self.embeddings = EmbeddingsClient()
        self._faiss: Optional[FaissIndex] = None
        self._ids: List[str] = self._load_ids()
        # Lazy TF-IDF cache
        self._tfidf = None
        self._tfidf_ids: List[str] = []
        self._tfidf_matrix = None
        # Local summarizer
        self._summarizer = None
        if pipeline is not None:
            model_name = os.environ.get("LOCAL_SUM_MODEL", "sshleifer/distilbart-cnn-12-6")
            try:
                self._summarizer = pipeline("summarization", model=model_name)
            except Exception:
                self._summarizer = None

    def _load_ids(self) -> List[str]:
        sidecar = self.index_path + ".ids"
        if os.path.exists(sidecar):
            with open(sidecar, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        return []

    def _save_ids(self) -> None:
        sidecar = self.index_path + ".ids"
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        with open(sidecar, "w", encoding="utf-8") as f:
            for _id in self._ids:
                f.write(_id + "\n")

    def _ensure_faiss(self, dim: int) -> None:
        if self._faiss is None:
            self._faiss = FaissIndex(self.index_path, dim)

    def _ensure_tfidf(self) -> None:
        if self._tfidf is not None and self._tfidf_matrix is not None and self._tfidf_ids:
            return
        docs = self.metadata.filter(limit=100000)
        texts = [(d.get("id"), (d.get("abstract") or d.get("title") or "")) for d in docs]
        self._tfidf_ids = [i for i, _ in texts]
        corpus = [t for _, t in texts]
        if not corpus:
            self._tfidf = None
            self._tfidf_matrix = None
            return
        self._tfidf = TfidfVectorizer(stop_words="english", max_features=50000)
        self._tfidf_matrix = self._tfidf.fit_transform(corpus)

    def _make_snippet(self, text: str, query: str, max_len: int = 240) -> str:
        if not text:
            return ""
        q = query.lower().split()
        t = text
        pos = min([t.lower().find(w) for w in q if t.lower().find(w) >= 0] + [0])
        start = max(0, pos - max_len // 3)
        end = min(len(t), start + max_len)
        snippet = t[start:end].strip()
        return ("..." + snippet + "...") if start > 0 or end < len(t) else snippet

    def semantic_search(self, query: str, top_k: int = 10, with_snippets: bool = False) -> List[Dict[str, Any]]:
        vec = np.array(self.embeddings.embed([query])[0], dtype=np.float32)
        self._ensure_faiss(len(vec))
        scores, idxs = self._faiss.search(vec.reshape(1, -1), top_k)
        results: List[Dict[str, Any]] = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx < 0 or idx >= len(self._ids):
                continue
            doc_id = self._ids[idx]
            docs = self.metadata.get_documents([doc_id])
            if not docs:
                continue
            d = docs[0]
            d["score"] = float(score)
            if with_snippets:
                d["snippet"] = self._make_snippet(d.get("abstract") or "", query)
            results.append(d)
        return results

    def keyword_search(self, query: str, top_k: int = 10, with_snippets: bool = False) -> List[Dict[str, Any]]:
        self._ensure_tfidf()
        if self._tfidf is None or self._tfidf_matrix is None or not self._tfidf_ids:
            return []
        q_vec = self._tfidf.transform([query])
        sims = linear_kernel(q_vec, self._tfidf_matrix).flatten()
        top_idx = sims.argsort()[::-1][:top_k]
        results: List[Dict[str, Any]] = []
        ids = [self._tfidf_ids[i] for i in top_idx]
        docs = {d.get("id"): d for d in self.metadata.get_documents(ids)}
        for i in top_idx:
            doc_id = self._tfidf_ids[i]
            d = docs.get(doc_id)
            if not d:
                continue
            d = dict(d)
            d["score"] = float(sims[i])
            if with_snippets:
                d["snippet"] = self._make_snippet(d.get("abstract") or "", query)
            results.append(d)
        return results

    def hybrid_search(self, query: str, top_k: int = 10, with_snippets: bool = False) -> List[Dict[str, Any]]:
        vec_hits = self.semantic_search(query, top_k=top_k * 2, with_snippets=False)
        kw_hits = self.keyword_search(query, top_k=top_k * 2, with_snippets=False)
        combined: Dict[str, Dict[str, Any]] = {}
        if vec_hits:
            v_scores = np.array([h["score"] for h in vec_hits])
            v_norm = (v_scores - v_scores.min()) / (v_scores.ptp() + 1e-9)
            for h, s in zip(vec_hits, v_norm):
                combined[h["id"]] = dict(h)
                combined[h["id"]]["_vscore"] = float(s)
        if kw_hits:
            k_scores = np.array([h["score"] for h in kw_hits])
            k_norm = (k_scores - k_scores.min()) / (k_scores.ptp() + 1e-9)
            for h, s in zip(kw_hits, k_norm):
                if h["id"] in combined:
                    combined[h["id"]]["_kscore"] = max(float(s), combined[h["id"]].get("_kscore", 0.0))
                else:
                    combined[h["id"]] = dict(h)
                    combined[h["id"]]["_kscore"] = float(s)
        rescored = []
        for doc_id, d in combined.items():
            v = d.get("_vscore", 0.0)
            k = d.get("_kscore", 0.0)
            score = 0.6 * v + 0.4 * k
            dd = dict(d)
            dd["score"] = float(score)
            if with_snippets:
                dd["snippet"] = self._make_snippet(dd.get("abstract") or "", query)
            dd.pop("_vscore", None)
            dd.pop("_kscore", None)
            rescored.append(dd)
        rescored.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return rescored[:top_k]

    def filter_metadata(self, organism=None, year_from=None, year_to=None, keywords=None, limit=50):
        return self.metadata.filter(organism, year_from, year_to, keywords, limit)

    def answer_query(self, query: str, context_ids: Optional[List[str]] = None, top_k: int = 10) -> Dict[str, Any]:
        if not context_ids:
            hits = self.hybrid_search(query, top_k=top_k, with_snippets=False)
            context_ids = [h["id"] for h in hits]
        docs = self.metadata.get_documents(context_ids)
        # Prefer Results/Conclusion later when section-aware is added; for now, use abstracts
        contexts = [d.get('abstract') or d.get('title') or '' for d in docs][:5]
        answer = self._summarize_local(query, contexts)
        citations = [
            {"id": d.get("id"), "title": d.get("title"), "url": d.get("url")}
            for d in docs
        ]
        return {"answer": answer, "citations": citations}

    def _summarize_local(self, query: str, contexts: List[str]) -> str:
        joined = "\n\n".join(contexts)
        if not joined.strip():
            return "No sufficient context found to summarize. Try a different query."
        # If summarizer available, use it; else return trimmed extractive text
        if self._summarizer is not None:
            try:
                text = joined[:4000]
                out = self._summarizer(text, max_length=220, min_length=90, do_sample=False)
                return out[0]["summary_text"]
            except Exception:
                pass
        # Fallback extractive
        return (joined[:800] + ("..." if len(joined) > 800 else ""))



