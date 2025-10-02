import os
import csv
import re
import argparse
from typing import Dict, Any, List, Optional

import numpy as np
from xml.etree import ElementTree as ET

from app.services.embeddings import EmbeddingsClient
from app.services.vector_store import FaissIndex, SQLiteMetadata

DEFAULT_META_CSV = "./database/outputs/metadata.csv"
DEFAULT_DB_PATH = os.environ.get("METADATA_DB_PATH", "./data/metadata.sqlite")
DEFAULT_INDEX_PATH = os.environ.get("VECTOR_INDEX_PATH", "./vector_store/faiss_index")

PMC_ID_RE = re.compile(r"PMC\d+")


def text_or_empty(node: Optional[ET.Element]) -> str:
    if node is None:
        return ""
    return ("".join(node.itertext()) or "").strip()


def parse_pmc_xml(xml_path: str) -> Dict[str, Any]:
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        # Common NLM JATS paths
        title = text_or_empty(root.find('.//article-title'))
        abstract = text_or_empty(root.find('.//abstract'))
        year = text_or_empty(root.find('.//pub-date/year'))
        try:
            year_int = int(year) if year else 0
        except Exception:
            year_int = 0
        url = None
        # grab pmcid if present
        pmc = None
        for id_el in root.findall('.//article-id'):
            if id_el.get('pub-id-type') == 'pmcid':
                pmc = id_el.text
                break
        if pmc and PMC_ID_RE.match(pmc):
            url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}/"
        return {
            "title": title,
            "abstract": abstract,
            "year": year_int,
            "url": url,
        }
    except Exception:
        return {"title": "", "abstract": "", "year": 0, "url": None}


def load_metadata_rows(csv_path: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Import database/outputs metadata + XML into engine store")
    parser.add_argument("--csv", default=DEFAULT_META_CSV, help="Path to database/outputs/metadata.csv")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite metadata db path")
    parser.add_argument("--index", default=DEFAULT_INDEX_PATH, help="FAISS index path")
    args = parser.parse_args()

    rows = load_metadata_rows(args.csv)
    if not rows:
        print("No rows in metadata.csv")
        return

    meta = SQLiteMetadata(args.db)
    docs: List[Dict[str, Any]] = []
    texts: List[str] = []

    for row in rows:
        pmcid = (row.get('pmcid') or '').strip()
        source_url = (row.get('source_url') or '').strip()
        xml_path = (row.get('xml_path') or '').strip()
        title_csv = (row.get('title') or '').strip()
        year_csv = row.get('year') or ''
        try:
            year_int = int(float(year_csv)) if year_csv not in ('', 'nan') else 0
        except Exception:
            year_int = 0

        title = title_csv
        abstract = ''
        url = source_url
        if xml_path and os.path.exists(xml_path):
            parsed = parse_pmc_xml(xml_path)
            title = parsed.get('title') or title
            abstract = parsed.get('abstract') or ''
            year_int = parsed.get('year') or year_int
            url = parsed.get('url') or url

        doc_id = pmcid or url or title or xml_path
        if not doc_id:
            continue
        d = {
            "id": doc_id,
            "title": title,
            "abstract": abstract,
            "year": year_int,
            "authors": '',
            "url": url,
            "organism": '',
            "keywords": [],
        }
        docs.append(d)
        texts.append(abstract or title)

    # Upsert metadata
    meta.upsert_documents(docs)

    # Build embeddings and index
    embedder = EmbeddingsClient()
    vecs = embedder.embed(texts)
    mat = np.array(vecs, dtype=np.float32)
    index = FaissIndex(args.index, dim=mat.shape[1])
    before, after = index.add(mat)
    index.save()

    # Save sidecar ids order
    sidecar = args.index + '.ids'
    os.makedirs(os.path.dirname(args.index), exist_ok=True)
    with open(sidecar, 'w', encoding='utf-8') as f:
        for d in docs:
            f.write(d['id'] + '\n')

    print(f"Imported {len(docs)} docs. Index before {before} → after {after}.")


if __name__ == "__main__":
    main()
