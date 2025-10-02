import os
from typing import List

import hashlib
import numpy as np

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:
    SentenceTransformer = None  # type: ignore


class EmbeddingsClient:
    def __init__(self) -> None:
        self.model_name = os.environ.get("LOCAL_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self._model = None
        if SentenceTransformer is not None:
            try:
                self._model = SentenceTransformer(self.model_name)
            except Exception:
                self._model = None

    def embed(self, texts: List[str]) -> List[List[float]]:
        if self._model is not None:
            vecs = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)  # type: ignore
            return vecs.astype(float).tolist()
        return self._embed_local_hash(texts)

    def _embed_local_hash(self, texts: List[str]) -> List[List[float]]:
        dim = 384
        vectors: List[List[float]] = []
        for t in texts:
            h = hashlib.sha256(t.encode("utf-8")).digest()
            np.random.seed(int.from_bytes(h[:4], "little"))
            v = np.random.normal(0, 1, dim)
            v = v / (np.linalg.norm(v) + 1e-9)
            vectors.append(v.astype(float).tolist())
        return vectors



