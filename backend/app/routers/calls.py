from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any, Optional
from core.ingestion.mongo_adapter import MongoTranscriptAdapter

router = APIRouter(prefix="/api/v1/calls", tags=["calls"])
adapter = MongoTranscriptAdapter()


@router.get("/tenants")
def get_tenants() -> List[Dict[str, str]]:
    """Returns list of active tenant databases."""
    return adapter.get_tenants()


@router.get("/")
def get_completed_calls(
    tenant_db: str = Query("sample_tenant_voicebot", description="Tenant DB name"),
    limit: int = Query(10, ge=1, le=50)
) -> List[Dict[str, Any]]:
    """Fetches completed calls with decrypted transcript turns."""
    calls = adapter.fetch_completed_calls(db_name=tenant_db, limit=limit)
    return calls
