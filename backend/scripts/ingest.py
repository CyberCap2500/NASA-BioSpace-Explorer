import os
import uuid
import pandas as pd
import numpy as np
from typing import List, Dict, Any

from app.services.embeddings import EmbeddingsClient
from app.services.vector_store import FaissIndex, SQLiteMetadata

CSV_PATH = os.environ.get("PUBLICATIONS_CSV", "./resources/SB_publication_PMC.csv")
INDEX_PATH = os.environ.get("VECTOR_INDEX_PATH", "./vector_store/faiss_index")
DB_PATH = os.environ.get("METADATA_DB_PATH", "./data/metadata.sqlite")


def normalize_text(t: Any) -> str:
    if pd.isna(t):
        return ""
    return str(t).strip()


def load_publications(csv_path: str) -> List[Dict[str, Any]]:
    df = pd.read_csv(csv_path)
    records: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        rid = normalize_text(row.get("pmcid")) or normalize_text(row.get("pmid")) or str(uuid.uuid4())
        title = normalize_text(row.get("title") or row.get("Title"))
        abstract = normalize_text(row.get("abstract") or row.get("Abstract"))
        year = int(row.get("year") or row.get("Year") or 0) if not pd.isna(row.get("year") or row.get("Year")) else 0
        authors = normalize_text(row.get("authors") or row.get("Authors"))
        url = normalize_text(row.get("url") or row.get("Url") or row.get("URL"))
        organism = normalize_text(row.get("organism") or row.get("Organism"))
        keywords_raw = normalize_text(row.get("keywords") or row.get("Keywords"))
        keywords = [k.strip() for k in keywords_raw.split(";") if k.strip()] if keywords_raw else []
        records.append({
            "id": rid,
            "title": title,
            "abstract": abstract,
            "year": year,
            "authors": authors,
            "url": url,
            "organism": organism,
            "keywords": keywords,
        })
    return records


def main() -> None:
    print("Loading publications from:", CSV_PATH)
    docs = load_publications(CSV_PATH)
    print(f"Loaded {len(docs)} records")

    # Persist metadata
    meta = SQLiteMetadata(DB_PATH)
    meta.upsert_documents(docs)

    # Build embeddings for abstracts (fallback to title if empty)
    texts = [d["abstract"] or d["title"] for d in docs]
    embedder = EmbeddingsClient()
    vecs = embedder.embed(texts)
    mat = np.array(vecs, dtype=np.float32)

    # Create FAISS index and add vectors
    index = FaissIndex(INDEX_PATH, dim=mat.shape[1])
    before, after = index.add(mat)
    index.save()

    # Save id ordering sidecar
    ids_path = INDEX_PATH + ".ids"
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    with open(ids_path, "w", encoding="utf-8") as f:
        for d in docs:
            f.write(d["id"] + "\n")

    print(f"Index vectors before: {before}, after: {after}")
    print("Done.")


if __name__ == "__main__":
    main()



