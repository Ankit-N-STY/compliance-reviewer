# Automated Compliance Reviewer for VoiceBot Calls — Project Context

## What this is

A personal AI-training project (Ankit Narkhede), run as a standalone side project —
**not** part of the production VoiceBot codebase and not delivered internally as a
feature. It follows a 15-session training curriculum (Generative AI fundamentals →
RAG → LangChain → LangGraph), building toward one working prototype.

**Use case:** Automatically review every completed VoiceBot call against required
compliance rules (e.g. disclosing it's an AI, not promising refund amounts, not
pressuring a customer after a refusal) and flag exactly where a rule was broken —
so a compliance team could verify in seconds instead of manually reviewing calls.
Replaces occasional manual spot-checks with full coverage.

**Design principle:** the LLM judges only within retrieved turns relevant to a
rule — it never invents a rule, and low confidence should surface as "flag for
manual review," never a guessed answer.

## Hard boundaries for this project

- **This is a separate git repo**, decoupled from the production `VoiceBot_Exotel`
  codebase. Do not import production application code into it.
- **Read-only against the dev DB.** No writes, no schema changes, no new indexes on
  the shared dev database. Treat it purely as an external, read-only data source.
- **The data is development/test data, not real customer data** — so this isn't a
  customer-PII governance problem. The actual constraint is simpler: the DB itself
  (connection, credentials, any raw dump) stays on the local machine only and is
  **never pushed to GitHub or committed to the repo.** Anything that does go into
  the repo (fixtures, examples in docs, etc.) should be the synthetic dataset, not
  a raw pull from the dev DB.
- Secrets (Mongo URI, Fernet key) live in a local `.env` on this machine only —
  **never commit them, never paste them into a chat/AI session, never hardcode them
  in a script that gets committed.**

## Where the source data lives (production system, for reference only)

The production app is a multi-tenant Flask + MongoDB + Celery VoiceBot platform
(Exotel/Twilio telephony). Relevant pieces for *reading* call data:

- **Master DB:** `voicebot-master` (customer registry, app config).
  - `customer_registry` collection maps `customer_name → db_name` — this is the
    only lookup you need to enumerate which per-customer DBs exist / find the
    right one for a given tenant. (`utils/utility.py:check_customer_in_registry`.)
- **Per-customer DB:** `voicebot_{sanitized_customer_name}` (one Mongo DB per
  tenant). Sanitization = `customer_name.lower().strip().replace(" ", "_")`.
- **Collection:** `campaign_call_info` — one document per **retry_key** (i.e. per
  lead/phone number in a campaign, not per call attempt — see overwrite note
  below). Relevant fields:
  - `call_sid`, `retry_key`, `campaign_name`, `status` (e.g. `completed`, `busy`,
    `no-answer`, `failed`, `exhausted`)
  - `encrypted_transcript` — a string of newline-separated lines like
    `BOT: gAAAAA...` / `CUSTOMER: gAAAAA...`, each value Fernet-encrypted.
  - `summary` — a dict of Fernet-encrypted field values (e.g. `call_summary`).
  - `extraction_intent` / `intent`, `total_time`, `call_history` (list, one entry
    per retry attempt — status/timing metadata only, see below).

  **Important overwrite behavior:** `call_sid` changes with every new retry
  attempt on the same `retry_key` doc, and `encrypted_transcript` is written via
  `$set` matched on the *current* `call_sid` (routes.py, `/vb/save-transcript`).
  That means the doc only ever holds the **latest attempt's** transcript —
  earlier attempts' transcript text is not retrievable from Mongo at all.
  `call_history` entries (pushed/updated by `utils/call_history_utils.py`) record
  per-attempt timing and status (`call_start`, `call_end`, `duration`,
  `lead_status_after`) but never transcript content. In practice this is fine
  for compliance review: filter on `status: "completed"` and you get the actual
  completed conversation, not a stale earlier attempt.
- **Decryption:** transcripts and summaries are encrypted with a single shared
  Fernet key (backend's own key, in `app/security_utils.py` as `FERNET_KEY` — a
  module-level constant, not a per-record key). A value is encrypted if it's a
  string starting with `gAAAA`; otherwise treat as plaintext already.
  Decryption logic (reference — reimplement standalone, don't import the app):
  ```python
  from cryptography.fernet import Fernet
  fernet = Fernet(FERNET_KEY)  # bytes, get this value out-of-band, never hardcode in a shared/committed file
  def decrypt_data(value):
      if not isinstance(value, str) or not value.startswith("gAAAA"):
          return value
      return fernet.decrypt(value.encode()).decode()
  ```
  A transcript line's speaker label (`BOT`/`CUSTOMER`) is plaintext; only the text
  after `:` is encrypted — split on the first `:`, decrypt the remainder.
- There is currently **no compliance-rules concept** anywhere in the production
  app — the rules config is something this project defines from scratch (e.g. a
  local `rules.yaml`: `rule_id`, `description`, which turns of a call are
  relevant, a couple of example violating/compliant snippets).
- An existing API endpoint, `GET /vb/get_transcript?stream_sid=...` (JWT-protected),
  returns the same encrypted transcript lines if API access is preferred over a
  direct DB connection — same decryption step applies either way.

## Recommended repo layout

Decided architecture: **separate React frontend + FastAPI backend** (not a
Streamlit throwaway) — built as its own step once the core engine already works
via CLI/notebooks, not in parallel with the early pipeline-building work.

```
compliance-reviewer/
  core/                  # framework-agnostic engine — the only part that changes
    ingestion/           #   data-source adapters (Mongo dev-DB adapter, synthetic-fixture adapter)
    engine/              #   retrieval -> judgment -> structured output (hand-rolled -> framework version -> agent/graph version, over time)
    rules/rules.yaml      #   hand-authored compliance rules (id, description, target turns, examples)
  backend/                # FastAPI — thin: imports core/, exposes REST endpoints, no business logic of its own
    app/main.py
    app/routers/
  frontend/               # React — violation dashboard: list calls, per-call flagged turns + quotes, confidence
  data/                   # local, gitignored — synthetic transcripts (primary) + any dev-DB samples pulled for testing
  sessions/
    session01_intro/
    session02_tokenization/
    ...                  # one folder per curriculum session (see table below), notebook/script + notes; imports from core/
  runs.jsonl              # experiment log: prompt version, model, latency, cost, precision/recall per run
  extract_samples.py      # occasional: read-only Mongo pull -> decrypt -> dump to data/ (local only, never committed)
  notes/                  # one file per functionality area — see "Notes convention" below
  .env                    # MONGO_URI (read-only user), FERNET_KEY — gitignored
  .gitignore              # must exclude data/, .env
  README.md               # mirrors the curriculum tracker table + status
```

## Notes convention

This is a learning-by-doing project — the point is for Ankit to understand every
piece, not just have working code appear. So `notes/` holds one markdown file per
functionality area (tokenization, embeddings/retrieval, prompt engineering, RAG,
LangChain, caching/rate-limits/quantization, structured outputs, retrieval
evaluation, guardrails, deployment/observability, LangGraph orchestration,
routing/fault-tolerance, backend API, frontend), not one running log. Each note
should explain, in plain language: what the piece does, why it's built that way,
the key concept(s) it teaches, decisions/tradeoffs made, and anything worth
remembering later. Update the relevant note as each piece is built — don't defer
it to the end.

**Sequencing note:** `core/` and the per-session notebooks are the actual
pipeline-building work — that's where most of the curriculum content lives.
`backend/` gets built once `core/` has a stable interface (this lines up
naturally with the curriculum's "package as a small service" step — see the
table below for exactly which one). `frontend/` comes last — it's a consumer of
`backend/`'s API, not something to design before the API shape is known.

## Auth & users

This app has **no relationship to Inteliconvo's user base, JWTs, or
`customer_registry`** — Inteliconvo (the source system) is used purely as a
read-only data source for call transcripts, nothing else crosses over.

- **For now: no auth at all.** No login, no roles, no API key — it's a
  single-person local demo. Don't build user management ahead of actually
  needing it.
- **If auth is ever needed later** (e.g. to demo this more broadly), it's this
  app's own, independent user/role system — its own users table, its own
  login, scoped to this app only. Never wire it to Inteliconvo's auth or
  attempt to reuse its accounts/JWTs.

## Curriculum (15 sessions, in order)

| # | Topic | Task | Output |
|---|-------|------|--------|
| 1 | Intro to Generative AI | Define problem/users/inputs/outputs/AI boundary; draw rules→retrieval→judgment→dashboard flow | 1-page architecture doc + diagram |
| 2 | Tokenisation fundamentals | Tokenize 5-10 sample transcripts; compare token cost of whole-transcript vs. just relevant turns for a rule like "AI disclosure" | Notebook + observations |
| 3 | Embeddings & vector similarity | Embed transcript turns; for "no pressure after refusal," verify turns after a customer's "no" retrieve as most relevant | Notebook + similarity results |
| 4 | Prompt engineering & versioning | Write prompt v1/v2/v3 (rule + retrieved turns → yes/no + quote); compare false pos/neg across 5 transcripts | Prompt versions + comparison |
| 5 | RAG architecture | Minimum viable slice: 1 hardcoded rule, 5 sample transcripts, chunk-by-turn, embed, retrieve top-k, manually verify | Working mini-RAG |
| 6 | LangChain | Rebuild Session 5 with LangChain loaders/splitters/retriever/prompt/output parser | LangChain RAG implementation |
| 7 | RAG vs fine-tuning & latency | Decide RAG vs fine-tuning (rules vary per tenant — RAG wins); benchmark retrieval vs. no-retrieval for 3 rules | Decision note + benchmark |
| 8 | Caching, rate limits, quantisation | Cache rule-check results per (call, rule); simulate rate limiting for 500 calls × 5 rules with backoff; compare full-precision vs. quantized model | Model comparison + caching report |
| 9 | Attention mechanisms | Analyze cost/latency for bulk end-of-day audits; document KV cache / sliding-window relevance | Context/latency analysis note |
| 10 | Structured outputs & hallucination reduction | Strict schema `{rule_id, violated, turn_index, quote, confidence}` + validation + retry/fallback; test on 5 tricky transcripts | Validated structured-output pipeline + tests |
| 11 | Retrieval scoring & evaluation | Hand-label 10-pair golden set; compare semantic vs. keyword retrieval, recall-focused | Golden dataset + evaluation |
| 12 | Guardrails & data governance | Mask PII in flagged quotes; test prompt-injection, subtle-violation, and ambiguous-rule adversarial cases | Guardrail/PII test suite |
| 13 | Deployment & observability | Package as a small service reading new calls from Mongo; log retrieval/judgment/latency per stage; identify one bottleneck | Deployable prototype + logs |
| 14 | LangGraph orchestration | Convert to graph: for-each-rule → retrieve → judge → self-check → conditional branch → aggregate; per-tenant rule sets as state | Working LangGraph workflow + diagram |
| 15 | Cost, routing & fault tolerance | Run same graph against a second tenant's rule set with zero code changes; add cheap/strong model routing; retry-once-then-flag-for-review fallback | Multi-tenant demo + notes |

## Open questions to resolve before/while extracting data

1. Will you get a dedicated **read-only** Mongo user for this, or reuse an existing
   read-write one? Push for read-only — removes the "don't modify" constraint from
   being just a self-imposed rule to an enforced one.
2. How will secrets (Mongo URI, Fernet key) get from this machine to the Windows
   machine? Use a private/secure channel you control (not pasted into an AI chat
   session) — e.g. a password manager, encrypted note, or typed by hand.
