from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from core.engine.embeddings import EmbeddingEngine
from core.engine.retriever import VectorRetriever
from core.storage.db import LocalDatabase

router = APIRouter(prefix="/api/v1/embeddings", tags=["embeddings"])
embedding_engine = EmbeddingEngine()
retriever = VectorRetriever(embedding_engine=embedding_engine)
db = LocalDatabase()


class EmbedRequest(BaseModel):
    text: str


class TurnInput(BaseModel):
    turn_index: int
    speaker: str
    text: str


class RetrieveRequest(BaseModel):
    turns: List[TurnInput]
    rule_query: str
    top_k: Optional[int] = 3


class SaveReviewRequest(BaseModel):
    call_sid: str
    tenant_name: str
    rule_id: str
    violated: bool
    turn_index: Optional[int] = None
    quote: Optional[str] = None
    confidence: str = "High"


@router.post("/embed")
def embed_text(req: EmbedRequest) -> Dict[str, Any]:
    """Generates 384-dimensional vector embedding for text."""
    vector = embedding_engine.embed_text(req.text)
    return {
        "text": req.text,
        "vector_dimensions": len(vector),
        "embedding_sample": vector[:10]  # First 10 dimensions sample
    }


@router.post("/retrieve")
def retrieve_relevant_turns(req: RetrieveRequest) -> Dict[str, Any]:
    """Retrieves top-k semantically relevant turns for a compliance rule query."""
    turns_dict = [t.model_dump() for t in req.turns]
    relevant_turns = retriever.retrieve_relevant_turns(
        turns=turns_dict,
        rule_query=req.rule_query,
        top_k=req.top_k or 3
    )
    # Clean out huge embedding arrays from API response JSON
    clean_turns = []
    for t in relevant_turns:
        item = {k: v for k, v in t.items() if k != "embedding"}
        clean_turns.append(item)

    return {
        "rule_query": req.rule_query,
        "retrieved_turns": clean_turns,
        "top_k": req.top_k or 3
    }


@router.post("/reviews")
def save_audit_review(req: SaveReviewRequest) -> Dict[str, Any]:
    """Saves a compliance review result into local database."""
    saved = db.save_review(req.model_dump())
    return {"status": "success", "review": saved}


@router.get("/reviews")
def get_audit_reviews(limit: int = Query(50, ge=1, le=100)) -> List[Dict[str, Any]]:
    """Fetches list of stored compliance reviews from local storage."""
    return db.get_all_reviews(limit=limit)
