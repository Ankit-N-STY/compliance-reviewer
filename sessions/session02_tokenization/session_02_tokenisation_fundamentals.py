import os
import sys
import json

# Ensure UTF-8 output handling on Windows terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from core.ingestion.mongo_adapter import MongoTranscriptAdapter
from core.engine.tokenizer import TokenizerEngine

def safe_repr(text: str) -> str:
    """Safely converts subword text for Windows console printing."""
    return repr(text.encode("ascii", "backslashreplace").decode("ascii"))

def main():
    print("=" * 80)
    print("SESSION 2: TOKENISATION FUNDAMENTALS & AI BOUNDARY SAVINGS BENCHMARK")
    print("=" * 80)

    # 1. Initialize Adapter and Tokenizer
    adapter = MongoTranscriptAdapter()
    tokenizer = TokenizerEngine(hf_model_name="gpt2", tiktoken_encoding="cl100k_base")

    # 2. Fetch completed sample calls
    calls = adapter.fetch_completed_calls("sample_tenant_voicebot", limit=10)
    print(f"\nLoaded {len(calls)} call transcripts for tokenization audit.\n")

    # 3. Demonstrate Subword Tokenization on a sample turn
    sample_text = "Hello! I am an AI assistant calling from Acme Hiring Solutions regarding your recent job application."
    print("--- 1. SUBWORD TOKENIZATION DEMO ---")
    print(f"Original Text:\n  \"{sample_text}\"\n")

    tiktoken_subwords = tokenizer.tokenize_with_subwords(sample_text, engine="tiktoken")
    print(f"Tiktoken (cl100k_base) Token Count: {len(tiktoken_subwords)}")
    print("Subword Tokens breakdown (first 10):")
    for subw, tid in tiktoken_subwords[:10]:
        print(f"  Token ID: {tid:<8} -> Subword: {safe_repr(subw)}")

    hf_subwords = tokenizer.tokenize_with_subwords(sample_text, engine="hf")
    print(f"\nHugging Face (gpt2) Token Count: {len(hf_subwords)}")
    print("Subword Tokens breakdown (first 10):")
    for subw, tid in hf_subwords[:10]:
        print(f"  Token ID: {tid:<8} -> Subword: {safe_repr(subw)}")

    # 4. Run Token Savings Analysis across all calls for AI Disclosure Rule
    print("\n" + "=" * 80)
    print("--- 2. CONTEXT WINDOW SAVINGS BENCHMARK FOR 'AI DISCLOSURE RULE' ---")
    print("Rule Definition: 'VoiceBot must disclose it is an AI within the first 2 turns.'")
    print("Comparison: Whole Transcript (All turns) vs AI Boundary Filtered (Turns 1-2 only)")
    print("=" * 80)

    total_full_tokens_tiktoken = 0
    total_filtered_tokens_tiktoken = 0

    total_full_tokens_hf = 0
    total_filtered_tokens_hf = 0

    benchmark_results = []

    print(f"\n{'Call SID':<35} | {'Total Turns':<11} | {'Full Tokens':<11} | {'Filtered (T1-2)':<15} | {'Savings %':<10}")
    print("-" * 90)

    for call in calls:
        call_sid = call.get("call_sid", "unknown")
        all_turns = call.get("turns", [])
        
        # Rule filter: AI Disclosure only needs first 2 turns
        filtered_turns = [t for t in all_turns if t.get("turn_index", 0) <= 2]

        savings = tokenizer.calculate_savings(all_turns, filtered_turns, rule_name="AI Disclosure Rule")
        
        full_tok_t = savings["tiktoken"]["full_tokens"]
        filt_tok_t = savings["tiktoken"]["filtered_tokens"]
        pct_t = savings["tiktoken"]["percentage_saved"]

        total_full_tokens_tiktoken += full_tok_t
        total_filtered_tokens_tiktoken += filt_tok_t

        total_full_tokens_hf += savings["huggingface"]["full_tokens"]
        total_filtered_tokens_hf += savings["huggingface"]["filtered_tokens"]

        print(f"{call_sid:<35} | {len(all_turns):<11} | {full_tok_t:<11} | {filt_tok_t:<15} | {pct_t:.1f}%")

        benchmark_results.append({
            "call_sid": call_sid,
            "turns_count": len(all_turns),
            "savings": savings
        })

    total_saved_tiktoken = total_full_tokens_tiktoken - total_filtered_tokens_tiktoken
    avg_pct_saved_tiktoken = (total_saved_tiktoken / total_full_tokens_tiktoken * 100) if total_full_tokens_tiktoken > 0 else 0

    total_saved_hf = total_full_tokens_hf - total_filtered_tokens_hf
    avg_pct_saved_hf = (total_saved_hf / total_full_tokens_hf * 100) if total_full_tokens_hf > 0 else 0

    print("-" * 90)
    print(f"{'TOTAL AUDIT BATCH':<35} | {'-':<11} | {total_full_tokens_tiktoken:<11} | {total_filtered_tokens_tiktoken:<15} | {avg_pct_saved_tiktoken:.1f}%")
    print("=" * 80)

    # 5. Financial & Latency Impact Analysis
    print("\n--- 3. FINANCIAL & COST SAVINGS QUANTIFICATION ---")
    print(f"Total Full Transcript Tokens (5 calls):      {total_full_tokens_tiktoken} tokens")
    print(f"Total AI Boundary Filtered Tokens (5 calls):  {total_filtered_tokens_tiktoken} tokens")
    print(f"Total Tokens Saved per batch:                 {total_saved_tiktoken} tokens ({avg_pct_saved_tiktoken:.2f}% reduction)")

    # Extrapolate for 10,000 calls/day audit
    calls_per_day = 10000
    avg_full_tokens_per_call = total_full_tokens_tiktoken / len(calls) if len(calls) > 0 else 0
    avg_filt_tokens_per_call = total_filtered_tokens_tiktoken / len(calls) if len(calls) > 0 else 0

    daily_full_tokens = avg_full_tokens_per_call * calls_per_day
    daily_filt_tokens = avg_filt_tokens_per_call * calls_per_day
    daily_saved_tokens = daily_full_tokens - daily_filt_tokens

    print(f"\nExtrapolation for daily compliance audit of {calls_per_day:,} calls:")
    print(f"  - Full Transcript approach:     {daily_full_tokens / 1e6:.2f} Million tokens/day")
    print(f"  - AI Boundary Filtered approach: {daily_filt_tokens / 1e6:.2f} Million tokens/day")
    print(f"  - Daily Context Reduction:      {daily_saved_tokens / 1e6:.2f} Million tokens saved/day ({avg_pct_saved_tiktoken:.1f}% less context overhead)")

    # Save benchmark artifact to data/
    out_dir = os.path.join("data")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "tokenization_benchmark_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "total_calls": len(calls),
                "tiktoken": {
                    "total_full_tokens": total_full_tokens_tiktoken,
                    "total_filtered_tokens": total_filtered_tokens_tiktoken,
                    "tokens_saved": total_saved_tiktoken,
                    "percentage_saved": round(avg_pct_saved_tiktoken, 2)
                },
                "huggingface": {
                    "model": "gpt2",
                    "total_full_tokens": total_full_tokens_hf,
                    "total_filtered_tokens": total_filtered_tokens_hf,
                    "tokens_saved": total_saved_hf,
                    "percentage_saved": round(avg_pct_saved_hf, 2)
                }
            },
            "calls": benchmark_results
        }, f, indent=2)

    print(f"\n[SUCCESS] Benchmark results saved to: {out_file}")

if __name__ == "__main__":
    main()
