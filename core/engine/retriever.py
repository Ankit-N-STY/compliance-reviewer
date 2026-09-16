from typing import List, Dict, Any, Optional
from core.engine.embeddings import EmbeddingEngine, cosine_similarity

class VectorRetriever:
    """
    Semantic Vector Retriever for VoiceBot compliance rules.
    Ranks call transcript turns by cosine similarity against compliance rule query vectors.
    """

    def __init__(self, embedding_engine: Optional[EmbeddingEngine] = None):
        self.embedding_engine = embedding_engine or EmbeddingEngine()

    def retrieve_relevant_turns(
        self,
        turns: List[Dict[str, Any]],
        rule_query: str,
        top_k: int = 3,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Embeds rule_query and candidate turns (if not already embedded),
        computes cosine similarity scores, and returns top-k highest scoring turns.
        """
        if not turns:
            return []

        # 1. Embed query text
        query_vector = self.embedding_engine.embed_text(rule_query)

        # 2. Ensure turns have embeddings
        turns_to_embed = [t for t in turns if "embedding" not in t or not t["embedding"]]
        if turns_to_embed:
            self.embedding_engine.embed_turns(turns_to_embed)

        # 3. Calculate similarity score for each turn
        scored_turns = []
        for turn in turns:
            turn_vec = turn.get("embedding", [])
            score = cosine_similarity(query_vector, turn_vec)
            
            # Create a copy with score attached
            scored_turn = dict(turn)
            scored_turn["similarity_score"] = round(score, 4)
            scored_turns.append(scored_turn)

        # 4. Sort descending by similarity score
        scored_turns.sort(key=lambda x: x["similarity_score"], reverse=True)

        # 5. Return top_k turns passing min_score threshold
        filtered = [t for t in scored_turns if t["similarity_score"] >= min_score]
        return filtered[:top_k]
