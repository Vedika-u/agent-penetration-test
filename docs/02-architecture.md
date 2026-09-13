# Architecture

## Data flow

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│ Attack Corpus     │ →  │ Attack Runner     │ →  │ Target Agent        │
│ (JailbreakBench,  │    │ (garak probes +   │    │ (built from scratch │
│ StrongREJECT,      │    │ custom injection   │    │ here: LangGraph,    │
│ deepset PI set)    │    │ payloads)          │    │ tools + memory,     │
│                    │    │                    │    │ run as an HTTP API) │
└─────────────────┘     └──────────────────┘     └──────────┬─────────┘
                                                              │ response
                                                              ▼
                                                   ┌────────────────────┐
                                                   │ Detection Layer     │
                                                   │ - grounding check   │
                                                   │ - attention/PI      │
                                                   │   classifier        │
                                                   │ - memory-integrity  │
                                                   │   check             │
                                                   │ - refusal detector  │
                                                   └──────────┬─────────┘
                                                              ▼
                                                   ┌────────────────────┐
                                                   │ Scorer              │
                                                   │ (StrongREJECT-style │
                                                   │ auto-eval: ASR,     │
                                                   │ precision/recall)   │
                                                   └──────────┬─────────┘
                                                              ▼
                                                   ┌────────────────────┐
                                                   │ Dashboard            │
                                                   │ (React/TS)           │
                                                   └────────────────────┘
```

## Components

### Target agent (built from scratch)
The system under test, purpose-built for this project rather than reused from another repo:

- **Orchestration**: a LangGraph state graph — `agent` node (LLM call, decides to respond or
  call a tool) → `tool` node (dispatches to one of the three tools below) → `memory` node
  (reads/writes the persistent store) → back to `agent`, looping until a final response.
- **Tools**:
  - `web_search` — the main indirect-injection surface (attacker content can arrive inside a
    tool result the agent then reasons over).
  - `notes` — a CRUD-style task/note store, backed by SQLite, that persists across turns. This
    is also the **memory-poisoning** surface: a malicious instruction written to a note in one
    turn can be read back and acted on in a later turn.
  - `calculator` — low-risk, included mainly so the agent has a benign tool to fall back to in
    control-condition tests.
- **Verification node**: a graph node that checks tool outputs and memory reads against the
  agent's own claims before they reach the final response — a minimal grounding check on day
  one, extended into the full detection layer in Phase 3 (same graph, not a bolted-on
  service).
- **Interface**: exposed over HTTP so the attack runner treats it as a black box, the same way
  it would treat any other target.

### Attack corpus
Public datasets, not hand-written prompts, so results are reproducible and comparable to
published baselines:
- JailbreakBench — 100 curated policy-violating behaviors + standardized scoring
- StrongREJECT — harmful-prompt dataset with an automated evaluator
- deepset prompt-injection dataset — quick classification baseline

### Attack runner
[garak](https://github.com/NVIDIA/garak) drives the target agent through its probe suite.
The runner is a thin wrapper that:
- Exposes the target agent as an HTTP endpoint garak can call
- Logs every (attack, response) pair with metadata (probe name, category, timestamp)
- Is swappable — the same runner should work against this project's own target agent, the
  email agent, or a third-party model with only a config change

### Detection layer
The part of the project that isn't just "run someone else's tool":
- A grounding/citation check, extending the target agent's own verification node rather than
  a separate service
- A memory-integrity check specific to the notes tool — flags a note whose content looks like
  an instruction rather than user data, since that's the project's memory-poisoning vector
- One purpose-built classifier — an attention-shift or embedding-similarity detector,
  informed by the Attention Tracker / PIShield papers (see `04-research-references.md`) —
  rather than only relying on garak's built-in judge
- Structured as an extension of the target agent's existing LangGraph graph (triage → check →
  verdict), not a separate pipeline

### Scorer
- Computes Attack Success Rate (ASR) per probe category, before and after the detection
  layer is applied
- Uses a StrongREJECT-style automated evaluator for scoring, with precision/recall reported
  against a labeled subset for validation

### Dashboard
- React + TypeScript + Tailwind — same stack as the existing portfolio, so the skillset
  transfers directly
- Shows: ASR by attack category, detector confusion matrix, and a handful of annotated
  example transcripts (attack prompt → agent response → verdict)
- Backed by real stored data (SQLite or Supabase/Postgres), not static JSON, so it reads as
  a live tool rather than a rendered report

## Tech stack

| Layer | Choice | Rationale |
|---|---|---|
| Target agent | Python + LangGraph, built from scratch in this repo | Full control over tools/memory/prompts as authored attack surface; no external agent dependency |
| Attack execution | Python + garak | Reuse a maintained, actively-updated probe library |
| Detection layer | Python, extends the target agent's LangGraph graph | Keeps verification in-graph rather than a bolted-on service |
| Storage | SQLite (dev) / Supabase Postgres (deployed) | Matches the email agent's existing backend choice; also backs the target agent's notes/memory store |
| Dashboard | React + TypeScript + Tailwind | Matches the portfolio site's stack |
| Deployment | Static dashboard (Vercel/GitHub Pages) + hosted API or precomputed results | Keep this reproducible and cheap to host |
