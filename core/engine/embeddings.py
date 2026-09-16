import os
import math
from typing import List, Dict, Any, Optional

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Computes cosine similarity between two numeric vectors: (a . b) / (||a|| * ||b||)."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)


class EmbeddingEngine:
    """
    Vector Embedding Engine using sentence-transformers (all-MiniLM-L6-v2).
    Generates 384-dimensional dense vector embeddings for semantic search.
    Runs 100% locally on CPU with zero API costs.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None

        if HAS_SENTENCE_TRANSFORMERS:
            try:
                # Loads model weights using standard PC User Cache (~80MB)
                self.model = SentenceTransformer(model_name)
            except Exception as e:
                print(f"Warning loading embedding model '{model_name}': {e}")

    def embed_text(self, text: str) -> List[float]:
        """Embeds a single string into a 384-dimensional float vector."""
        if self.model:
            vector = self.model.encode(text, convert_to_numpy=True)
            return vector.tolist()
        # Simple fallback synthetic vector if model isn't available
        return [0.1] * 384

    def embed_turns(self, turns: List[Dict[str, Any]], call_sid: str = "") -> List[Dict[str, Any]]:
        """
        Embeds a list of call turns, attaching an 'embedding' vector field to each turn dict.
        Format of string embedded per turn: "Speaker: Text"
        """
        texts_to_embed = [f"{t.get('speaker', 'UNKNOWN')}: {t.get('text', '')}" for t in turns]

        if self.model and texts_to_embed:
            vectors = self.model.encode(texts_to_embed, convert_to_numpy=True)
            for idx, turn in enumerate(turns):
                turn["embedding"] = vectors[idx].tolist()
        else:
            for turn in turns:
                turn["embedding"] = [0.1] * 384

        return turns
