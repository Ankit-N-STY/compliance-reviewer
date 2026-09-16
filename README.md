# Automated Compliance Reviewer for VoiceBot Calls

Personal AI-training project (Ankit Narkhede). Standalone side project, **not**
part of the production VoiceBot codebase.

**Use case:** automatically review completed VoiceBot calls against
compliance rules (e.g. disclosing it's an AI, not promising refund amounts,
not pressuring a customer after a refusal), flagging exactly where a rule was
broken. Low-confidence judgments surface as "flag for manual review," never a
guess.

Full background, architecture, data-source schema, and working conventions
live in [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) — see that file for the
canonical source of truth.

## Repo layout

- `core/` — framework-agnostic engine (data-source adapters, retrieval ->
  judgment -> structured output). This is the part that changes across
  sessions.
- `backend/` — FastAPI, built once `core/` is stable. Thin: imports `core/`,
  exposes REST endpoints.
- `frontend/` — React violation dashboard, built last.
- `sessions/` — one folder per curriculum session below, notebook/script +
  notes, imports from `core/`.
- `notes/` — one markdown file per functionality area (tokenization,
  embeddings/retrieval, prompt engineering, RAG, LangChain, etc.), written as
  each piece is built.
- `data/` — local, gitignored. Synthetic transcripts + any dev-DB samples
  pulled for testing. Never committed.
- `.env` — local secrets (Mongo URI, Fernet key). Gitignored, never committed.

## Status

Scaffolding complete. Starting Session 1.

## Curriculum

| # | Topic | Task | Output | Status |
|---|-------|------|--------|--------|
| 1 | Intro to Generative AI | Define problem/users/inputs/outputs/AI boundary; draw rules→retrieval→judgment→dashboard flow | 1-page architecture doc + diagram | In progress |
| 2 | Tokenisation fundamentals | Tokenize 5-10 sample transcripts; compare token cost of whole-transcript vs. just relevant turns for a rule like "AI disclosure" | Notebook + observations | Not started |
| 3 | Embeddings & vector similarity | Embed transcript turns; for "no pressure after refusal," verify turns after a customer's "no" retrieve as most relevant | Notebook + similarity results | Not started |
| 4 | Prompt engineering & versioning | Write prompt v1/v2/v3 (rule + retrieved turns → yes/no + quote); compare false pos/neg across 5 transcripts | Prompt versions + comparison | Not started |
| 5 | RAG architecture | Minimum viable slice: 1 hardcoded rule, 5 sample transcripts, chunk-by-turn, embed, retrieve top-k, manually verify | Working mini-RAG | Not started |
| 6 | LangChain | Rebuild Session 5 with LangChain loaders/splitters/retriever/prompt/output parser | LangChain RAG implementation | Not started |
| 7 | RAG vs fine-tuning & latency | Decide RAG vs fine-tuning (rules vary per tenant — RAG wins); benchmark retrieval vs. no-retrieval for 3 rules | Decision note + benchmark | Not started |
| 8 | Caching, rate limits, quantisation | Cache rule-check results per (call, rule); simulate rate limiting for 500 calls × 5 rules with backoff; compare full-precision vs. quantized model | Model comparison + caching report | Not started |
| 9 | Attention mechanisms | Analyze cost/latency for bulk end-of-day audits; document KV cache / sliding-window relevance | Context/latency analysis note | Not started |
| 10 | Structured outputs & hallucination reduction | Strict schema `{rule_id, violated, turn_index, quote, confidence}` + validation + retry/fallback; test on 5 tricky transcripts | Validated structured-output pipeline + tests | Not started |
| 11 | Retrieval scoring & evaluation | Hand-label 10-pair golden set; compare semantic vs. keyword retrieval, recall-focused | Golden dataset + evaluation | Not started |
| 12 | Guardrails & data governance | Mask PII in flagged quotes; test prompt-injection, subtle-violation, and ambiguous-rule adversarial cases | Guardrail/PII test suite | Not started |
| 13 | Deployment & observability | Package as a small service reading new calls from Mongo; log retrieval/judgment/latency per stage; identify one bottleneck | Deployable prototype + logs | Not started |
| 14 | LangGraph orchestration | Convert to graph: for-each-rule → retrieve → judge → self-check → conditional branch → aggregate; per-tenant rule sets as state | Working LangGraph workflow + diagram | Not started |
| 15 | Cost, routing & fault tolerance | Run same graph against a second tenant's rule set with zero code changes; add cheap/strong model routing; retry-once-then-flag-for-review fallback | Multi-tenant demo + notes | Not started |

## Environment

- Python 3.11.6
- Node v22.13.1 / npm 11.7.0
- Mongo access: TBD (see open questions in PROJECT_CONTEXT.md)

