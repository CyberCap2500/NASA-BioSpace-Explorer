from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional
import os

from app.services.search import SearchService

app = FastAPI(title="BioSpace Explorer API", version="0.1.1")

search_service = SearchService(
    index_path=os.environ.get("VECTOR_INDEX_PATH", "./vector_store/faiss_index"),
    metadata_db_path=os.environ.get("METADATA_DB_PATH", "./data/metadata.sqlite"),
)


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    mode: str = "vector"  # vector | keyword | hybrid


class SummarizeRequest(BaseModel):
    query: str
    context_ids: Optional[List[str]] = None
    top_k: int = 10


class FilterRequest(BaseModel):
    organism: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    keywords: Optional[List[str]] = None
    limit: int = 50


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/search")
async def search(req: SearchRequest):
    if req.mode == "vector":
        results = search_service.semantic_search(req.query, top_k=req.top_k, with_snippets=True)
    elif req.mode == "keyword":
        results = search_service.keyword_search(req.query, top_k=req.top_k, with_snippets=True)
    else:
        results = search_service.hybrid_search(req.query, top_k=req.top_k, with_snippets=True)
    return {"results": results, "mode": req.mode}


@app.post("/summarize")
async def summarize(req: SummarizeRequest):
    answer = search_service.answer_query(
        query=req.query,
        context_ids=req.context_ids,
        top_k=req.top_k,
    )
    return answer


@app.post("/filter")
async def filter_endpoint(req: FilterRequest):
    items = search_service.filter_metadata(
        organism=req.organism,
        year_from=req.year_from,
        year_to=req.year_to,
        keywords=req.keywords,
        limit=req.limit,
    )
    return {"results": items}



