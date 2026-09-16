# Tokenisation Fundamentals & Context Optimization

## What it is

Tokenization is the process of breaking raw text strings into numerical chunks ("tokens") that an LLM's neural network can process. Words are rarely single tokens; instead, modern LLMs use **Byte-Pair Encoding (BPE)** or **WordPiece** to split text into subword units, spaces, and punctuation marks.

In this session, we built local tokenization tools, integrated a read-only MongoDB adapter for VoiceBot call transcripts, built FastAPI endpoints, and benchmarked the exact token savings achieved by filtering call turns before LLM judgment (the AI Boundary principle).

---

## Key Concepts

### 1. Subwords vs. Words
- A single English word can be 1, 2, or 3+ tokens depending on rarity and capitalization.
- Example: `"Hello!"` $\rightarrow$ `['Hello', '!']` (2 tokens).
- Example: `"Acme"` $\rightarrow$ `[' Ac', 'me']` in GPT-2 BPE encoding.

### 2. Byte-Pair Encoding (BPE)
- BPE builds a vocabulary of frequent character sequences. Common prefixes/suffixes (e.g. `ing`, `tion`, ` AI`) are assigned single token IDs.
- Spaces are often encoded as leading characters (e.g., HuggingFace uses `Ġ` / `\u0120` to represent a space before a word).

### 3. Dual Tokenizer Engine: HuggingFace vs. Tiktoken
- **`tiktoken` (`cl100k_base`)**: OpenAI's BPE encoding used in GPT-4 / GPT-4o. Very dense vocabulary (~100k tokens), resulting in slightly fewer tokens for code and technical terms.
- **HuggingFace (`gpt2`)**: Open-source baseline BPE tokenizer. Demonstrates standard open-source token splitting mechanics running 100% locally.

---

## Benchmark Results: Full Transcript vs. AI Boundary Filtering

Rule evaluated: **"VoiceBot must disclose it is an AI within the first 2 turns."**

| Call SID | Total Turns | Full Transcript Tokens | Turn-Filtered Tokens (Turns 1–2) | Token Savings % |
|---|---|---|---|---|
| `sample_call_001_compliant` | 6 turns | 125 tokens | 45 tokens | **64.0%** |
| `sample_call_002_missing_ai_disclosure` | 6 turns | 110 tokens | 42 tokens | **61.8%** |
| `sample_call_003_unauthorized_refund_promise` | 8 turns | 151 tokens | 40 tokens | **73.5%** |
| `sample_call_004_pressure_after_refusal` | 10 turns | 190 tokens | 28 tokens | **85.3%** |
| `sample_call_005_long_support_call` | 16 turns | 316 tokens | 46 tokens | **85.4%** |
| **BATCH TOTAL (5 Calls)** | **46 turns** | **892 tokens** | **201 tokens** | **77.5% reduction** |

---

## Why Built This Way & Tradeoffs

1. **AI Boundary Context Savings**:
   - Sending full 16-turn call transcripts for a rule that only concerns the introduction wastes 85%+ of your context window.
   - For a compliance system auditing 10,000 calls per day, filtering turns saves **1.38 Million tokens per day**.
2. **FastAPI Integration**:
   - Exposed endpoints under `/api/v1/tokenization/tokenize` and `/api/v1/tokenization/savings-benchmark` so the React frontend can inspect token counts and savings in real time.
3. **100% Free & Local Execution**:
   - Both `tiktoken` and HuggingFace `AutoTokenizer` execute locally on CPU with zero network dependency, zero API keys, and \$0 cost.

---

## API Endpoints (`FastAPI`)

- `POST /api/v1/tokenization/tokenize`: Tokenizes input text and returns subword breakdown.
- `POST /api/v1/tokenization/savings-benchmark`: Calculates token savings between full and filtered turns.
- `GET /api/v1/calls/`: Fetches completed call transcripts with decrypted turns.
- `GET /api/v1/calls/tenants`: Lists active customer tenants from `voicebot-master`.
