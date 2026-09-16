# Architecture & the AI boundary

## What it is

Before writing any retrieval or prompt code, we scoped the system: who uses
it, what goes in, what comes out, and — the one GenAI-specific idea — exactly
where the LLM's judgment starts and ends.

## Why built this way

LLMs are the least predictable, least testable part of any pipeline. The
fewer decisions you hand to the LLM, the smaller the surface area for
hallucination, and the more of the system you *can* unit test normally. So
the discipline is: push as much as possible (which rules exist, which turns
are candidates, how results get aggregated and displayed) into deterministic
code, and leave the LLM exactly one narrow, checkable decision — "given this
rule and these candidate turns, was it violated, and where."

## Key concept: the AI boundary

A line drawn around the smallest possible LLM responsibility. Everything
outside it must be inspectable/testable without ever calling the model.
Concretely here: retrieval (Session 3) shortlists candidate turns without an
LLM; only the shortlisted turns + one rule ever reach the model; the model
never sees the whole rule set or the whole transcript at once.

This is also *why* "low confidence -> flag for manual review" is a real
design requirement and not just a nice-to-have: because the LLM's job is
deliberately narrow, an honest "I'm not sure" inside that narrow job is more
useful than a guess would be.

## Decisions / tradeoffs

- Retrieval is deterministic (keyword/embedding search), not an LLM call —
  keeps cost down and keeps "what's relevant" auditable.
- Rules are hand-authored data (`rules.yaml`), never inferred by the model.
- Output schema is fixed per (call, rule) pair:
  `{rule_id, violated, turn_index, quote, confidence}` — decided now so
  every later session (prompting, structured outputs, evaluation) targets the
  same shape instead of drifting.

## See also

- `sessions/session01_intro/architecture.md` — the actual 1-pager + diagram.
- `PROJECT_CONTEXT.md` — canonical spec this session's scoping is drawn from.
