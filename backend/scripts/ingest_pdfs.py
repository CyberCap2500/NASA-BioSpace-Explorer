import os
import uuid
from typing import List, Dict, Any

import numpy as np
from pypdf import PdfReader

from app.services.embeddings import EmbeddingsClient
from app.services.vector_store import FaissIndex, SQLiteMetadata

PDF_DIR = os.environ.get("ARTICLES_DIR", "./articles_pdf")
INDEX_PATH = os.environ.get("VECTOR_INDEX_PATH", "./vector_store/faiss_index")
DB_PATH = os.environ.get("METADATA_DB_PATH", "./data/metadata.sqlite")
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200


def read_pdf_text(path: str) -> str:
    try:
        reader = PdfReader(path)
        texts = []
        for page in reader.pages:
            t = page.extract_text() or ""
            texts.append(t)
        return "\n".join(texts).strip()
    except Exception:
        return ""


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
        if start < 0:
            start = 0
        if start >= len(text):
            break
    return chunks


def build_docs_from_pdfs(pdf_dir: str) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for root, _, files in os.walk(pdf_dir):
        for f in files:
            if not f.lower().endswith(".pdf"):
                continue
            path = os.path.join(root, f)
            base = os.path.splitext(f)[0]
            url = None
            full_text = read_pdf_text(path)
            if not full_text:
                continue
            for idx, chunk in enumerate(chunk_text(full_text)):
                doc_id = f"{base}::chunk{idx}"
                docs.append({
                    "id": doc_id,
                    "title": base,
                    "abstract": chunk,
                    "year": 0,
                    "authors": "",
                    "url": url or path,
                    "organism": "",
                    "keywords": [],
                })
    return docs


def main() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    docs = build_docs_from_pdfs(PDF_DIR)
    if not docs:
        print("No PDF content found.")
        return
    print(f"Prepared {len(docs)} chunks from PDFs")

    metadata = SQLiteMetadata(DB_PATH)
    metadata.upsert_documents(docs)

    texts = [d["abstract"] or d["title"] for d in docs]
    embedder = EmbeddingsClient()
    vecs = embedder.embed(texts)
    mat = np.array(vecs, dtype=np.float32)

    index = FaissIndex(INDEX_PATH, dim=mat.shape[1])
    before, after = index.add(mat)
    index.save()

    ids_path = INDEX_PATH + ".ids"
    with open(ids_path, "w", encoding="utf-8") as f:
        for d in docs:
            f.write(d["id"] + "\n")

    print(f"Index vectors before: {before}, after: {after}")
    print("Done.")


if __name__ == "__main__":
    main()

