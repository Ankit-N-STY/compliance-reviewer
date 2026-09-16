import os
import json
from typing import List, Dict, Any, Optional
from core.ingestion.decryption import FernetDecryptor

class MongoTranscriptAdapter:
    """
    Read-only Mongo adapter for VoiceBot call transcripts.
    Strictly performs read queries (find_one, find). Zero write operations.
    Falls back to local json fixtures if Mongo URI is not configured.
    """

    def __init__(self, mongo_uri: Optional[str] = None, fernet_key: Optional[str] = None):
        self.mongo_uri = mongo_uri or os.getenv("MONGO_URI")
        self.decryptor = FernetDecryptor(key=fernet_key)
        self.client = None
        
        if self.mongo_uri:
            try:
                from pymongo import MongoClient
                self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=3000)
            except Exception as e:
                print(f"Mongo Connection Warning: {e}. Will use local sample data fallback.")

    def get_tenants(self) -> List[Dict[str, str]]:
        """Fetch list of tenant customers and their DB names from master DB."""
        if not self.client:
            return [{"customer_name": "Sample Tenant", "db_name": "sample_tenant_voicebot"}]
        
        try:
            master_db = self.client["voicebot-master"]
            registry = master_db["customer_registry"]
            docs = registry.find({"status": "active"}, {"customer_name": 1, "db_name": 1, "_id": 0})
            return list(docs)
        except Exception as e:
            print(f"Error reading customer_registry: {e}")
            return []

    def fetch_completed_calls(self, db_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch completed calls with transcripts from a tenant DB."""
        if not self.client:
            return self._load_local_sample_calls()[:limit]

        try:
            tenant_db = self.client[db_name]
            collection = tenant_db["campaign_call_info"]
            cursor = collection.find(
                {"status": "completed", "encrypted_transcript": {"$ne": None}},
                limit=limit
            )
            
            parsed_calls = []
            for doc in cursor:
                parsed_call = self.parse_call_document(doc)
                parsed_calls.append(parsed_call)
            return parsed_calls
        except Exception as e:
            print(f"Error fetching calls from {db_name}: {e}")
            return self._load_local_sample_calls()[:limit]

    def parse_call_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Parses raw call document, decrypting encrypted_transcript line by line into turns."""
        raw_transcript = doc.get("encrypted_transcript", "")
        turns = []
        
        if raw_transcript:
            lines = raw_transcript.strip().split("\n")
            for idx, line in enumerate(lines, start=1):
                turn_data = self.decryptor.decrypt_transcript_line(line)
                turn_data["turn_index"] = idx
                turns.append(turn_data)

        return {
            "call_sid": str(doc.get("call_sid")) if doc.get("call_sid") else None,
            "retry_key": str(doc.get("retry_key")) if doc.get("retry_key") else None,
            "campaign_name": doc.get("campaign_name"),
            "status": doc.get("status"),
            "turns": turns,
            "turn_count": len(turns)
        }

    def _load_local_sample_calls(self) -> List[Dict[str, Any]]:
        """Fallback helper to load local sample calls from data/transcripts/sample_calls.json."""
        filepath = os.path.join("data", "transcripts", "sample_calls.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
