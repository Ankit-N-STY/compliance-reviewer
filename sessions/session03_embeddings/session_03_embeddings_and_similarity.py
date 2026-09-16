import os
import sys
import json

# Ensure UTF-8 console printing on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from core.ingestion.mongo_adapter import MongoTranscriptAdapter
from core.engine.embeddings import EmbeddingEngine
from core.engine.retriever import VectorRetriever
from core.storage.db import LocalDatabase


def main():
    print("=" * 80)
    print("SESSION 3: EMBEDDINGS & VECTOR SIMILARITY BENCHMARK")
    print("Rule Target: 'No pressure after customer refusal'")
    print("=" * 80)

    # 1. Initialize core components
    adapter = MongoTranscriptAdapter()
    engine = EmbeddingEngine(model_name="all-MiniLM-L6-v2")
    retriever = VectorRetriever(embedding_engine=engine)
    db = LocalDatabase()

    # 2. Fetch sample call transcripts
    calls = adapter.fetch_completed_calls("sample_tenant_voicebot", limit=10)
    print(f"\nLoaded {len(calls)} call transcripts for vector search audit.")

    # Rule query string for semantic vector search
    rule_query = "Customer refuses offer, says no, stop calling, or not interested"
    print(f"Vector Search Query: \"{rule_query}\"\n")

    all_scored_turns = []

    for call in calls:
        call_sid = call.get("call_sid", "unknown")
        turns = call.get("turns", [])
        
        # Retrieve ranked turns using vector cosine similarity
        ranked_turns = retriever.retrieve_relevant_turns(turns, rule_query, top_k=len(turns))
        
        for t in ranked_turns:
            all_scored_turns.append({
                "call_sid": call_sid,
                "turn_index": t.get("turn_index"),
                "speaker": t.get("speaker"),
                "text": t.get("text"),
                "similarity_score": t.get("similarity_score")
            })

    # Sort all turns across all calls by similarity score
    all_scored_turns.sort(key=lambda x: x["similarity_score"], reverse=True)

    print("=" * 80)
    print("--- 1. TOP 5 RELEVANT MATCHES (High Vector Similarity) ---")
    print("=" * 80)

    top_5 = all_scored_turns[:5]
    for idx, match in enumerate(top_5, start=1):
        print(f"Match #{idx} [Score: {match['similarity_score']:.4f}]")
        print(f"  Call SID: {match['call_sid']} | Turn {match['turn_index']} [{match['speaker']}]")
        print(f"  Utterance: \"{match['text']}\"\n")

    print("=" * 80)
    print("--- 2. TOP 5 IRRELEVANT MATCHES (Low Vector Similarity) ---")
    print("=" * 80)

    bottom_5 = all_scored_turns[-5:]
    for idx, match in enumerate(bottom_5, start=1):
        print(f"Match #{idx} [Score: {match['similarity_score']:.4f}]")
        print(f"  Call SID: {match['call_sid']} | Turn {match['turn_index']} [{match['speaker']}]")
        print(f"  Utterance: \"{match['text']}\"\n")

    # 3. Simulate saving audit review result for the refusal call
    refusal_call = next((c for c in calls if "pressure_after_refusal" in c.get("call_sid", "")), None)
    if refusal_call:
        top_refusal_turn = retriever.retrieve_relevant_turns(refusal_call.get("turns", []), rule_query, top_k=1)[0]
        review_record = {
            "call_sid": refusal_call.get("call_sid"),
            "tenant_name": "sample_tenant_voicebot",
            "rule_id": "rule_no_pressure_after_refusal",
            "violated": True,
            "turn_index": top_refusal_turn.get("turn_index"),
            "quote": top_refusal_turn.get("text"),
            "confidence": "High",
            "similarity_score": top_refusal_turn.get("similarity_score")
        }
        db.save_review(review_record)
        print(f"[SUCCESS] Audit review persisted to local database: {review_record['call_sid']}")

    # 4. Save benchmark output to data/
    out_dir = os.path.join("data")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "embeddings_benchmark_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "rule_query": rule_query,
            "total_turns_evaluated": len(all_scored_turns),
            "top_5_relevant_matches": top_5,
            "top_5_irrelevant_matches": bottom_5
        }, f, indent=2)

    print(f"\n[SUCCESS] Vector embeddings benchmark saved to: {out_file}")

if __name__ == "__main__":
    main()
