import os
import json
import time
from typing import List, Dict, Any, Optional

class LocalDatabase:
    """
    Local Database storage manager for compliance reviewer.
    Saves compliance audit reviews and cached turn vector embeddings.
    Tries connecting to local MongoDB (mongodb://localhost:27017/compliance_reviewer_db)
    and gracefully falls back to local JSON storage in data/db/ if local Mongo is unavailable.
    """

    def __init__(self, mongo_uri: Optional[str] = None):
        self.mongo_uri = mongo_uri or os.getenv("LOCAL_MONGO_URI", "mongodb://localhost:27017")
        self.db_name = "compliance_reviewer_db"
        self.client = None
        self.use_mongo = False

        try:
            from pymongo import MongoClient
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=1500)
            # Test ping
            self.client.admin.command('ping')
            self.use_mongo = True
            print(f"[Storage] Connected to local MongoDB at {self.mongo_uri}/{self.db_name}")
        except Exception:
            self.use_mongo = False
            self.db_dir = os.path.join("data", "db")
            os.makedirs(self.db_dir, exist_ok=True)
            print("[Storage] Local MongoDB not detected. Using local JSON storage fallback in data/db/")

    # --- REVIEWS COLLECTION ---
    def save_review(self, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves a compliance review result."""
        review_data["created_at"] = review_data.get("created_at") or time.strftime("%Y-%m-%d %H:%M:%S")

        if self.use_mongo and self.client:
            db = self.client[self.db_name]
            db["call_reviews"].insert_one(dict(review_data))
            return review_data
        else:
            filepath = os.path.join("data", "db", "call_reviews.json")
            reviews = self.get_all_reviews()
            reviews.append(review_data)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(reviews, f, indent=2)
            return review_data

    def get_all_reviews(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetches stored compliance reviews."""
        if self.use_mongo and self.client:
            db = self.client[self.db_name]
            cursor = db["call_reviews"].find({}, {"_id": 0}).limit(limit)
            return list(cursor)
        else:
            filepath = os.path.join("data", "db", "call_reviews.json")
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)[:limit]
            return []

    # --- EMBEDDINGS CACHE COLLECTION ---
    def save_turn_embedding(self, turn_key: str, embedding: List[float], text: str) -> None:
        """Caches turn embedding vector locally."""
        record = {"turn_key": turn_key, "embedding": embedding, "text": text}
        if self.use_mongo and self.client:
            db = self.client[self.db_name]
            db["turn_embeddings"].update_one({"turn_key": turn_key}, {"$set": record}, upsert=True)
        else:
            filepath = os.path.join("data", "db", "turn_embeddings.json")
            cache = self.get_cached_embeddings()
            cache[turn_key] = record
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2)

    def get_cached_embeddings(self) -> Dict[str, Any]:
        """Loads cached embeddings dictionary."""
        if self.use_mongo and self.client:
            db = self.client[self.db_name]
            cursor = db["turn_embeddings"].find({}, {"_id": 0})
            return {doc["turn_key"]: doc for doc in cursor}
        else:
            filepath = os.path.join("data", "db", "turn_embeddings.json")
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
